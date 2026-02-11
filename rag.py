import os
import json
import urllib.request
import ssl
from dotenv import load_dotenv

# --- RAG & DATABASE LIBRARIES ---
from langchain_community.vectorstores import Chroma
# Switched to HuggingFace (Local & Free) to fix API Errors
from langchain_community.embeddings import HuggingFaceEmbeddings 
from langchain_core.documents import Document

load_dotenv()

# --- CONFIGURATION ---
DB_FOLDER = "chroma_db"
DATA_FILE = "prepared_chunks.json"

# --- 1. SETUP EMBEDDINGS (LOCAL) ---
# This downloads a small, fast model to your laptop. No API Key needed for this part.
print("⚙️ Initializing Local Embeddings (all-MiniLM-L6-v2)...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# --- 2. GET OR CREATE DATABASE ---
def get_or_create_vector_db():
    # If database exists, load it
    if os.path.exists(DB_FOLDER) and os.listdir(DB_FOLDER):
        print(f"✅ Loading existing database from {DB_FOLDER}...")
        return Chroma(persist_directory=DB_FOLDER, embedding_function=embeddings)
    
    # If not, create it
    print(f"⚠️ Database not found. Creating new one from {DATA_FILE}...")
    
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"CRITICAL ERROR: {DATA_FILE} not found! Cannot build database.")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    documents = []
    for item in data:
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        if text:
            documents.append(Document(page_content=text))

    vector_store = Chroma.from_documents(
        documents=documents, 
        embedding=embeddings, 
        persist_directory=DB_FOLDER
    )
    print(f"✅ Database created successfully!")
    return vector_store

# Initialize Database
vector_store = get_or_create_vector_db()

# --- 3. ANSWER FUNCTION WITH GUARDRAILS ---
def answer_question(question):
    print(f"\n🔍 Analyzing Question: {question}")
    
    # --- GUARDRAIL: SIMILARITY THRESHOLD ---
    results_with_scores = vector_store.similarity_search_with_score(question, k=3)

    if not results_with_scores:
        return "I am sorry, but I do not have information on this topic."

    best_doc, best_score = results_with_scores[0]
    
    # NOTE: For HuggingFace/L2 Distance, LOWER score is BETTER.
    # 0.0 = Exact Match. > 1.0 = Bad Match.
    # We use a threshold of 1.3 for this model.
    SIMILARITY_THRESHOLD = 1.4
    
    print(f"   Best Match Score: {best_score:.4f}") 

    if best_score > SIMILARITY_THRESHOLD:
        print("   ⛔ Guardrail Blocked! Question is irrelevant.")
        return "I am sorry, but my knowledge is strictly limited to my life, the Constitution, and social reform. I cannot answer this."

    # --- PREPARE CONTEXT ---
    context_text = "\n\n".join([doc.page_content for doc, _ in results_with_scores])

  # --- STRICT SYSTEM PROMPT ---
    prompt_text = f"""
    You are the digital avatar of Dr. B. R. Ambedkar.
    
    CONTEXT from Database:
    {context_text}
    
    STRICT RULES:
    1. IDENTITY: If asked "Who are you?", ALWAYS answer: "I am Dr. B. R. Ambedkar, the Father of the Indian Constitution and a social reformer." (You do not need context for this).
    2. RESTRICTION: For all other questions, answer ONLY using the provided CONTEXT. 
    3. REFUSAL: If the answer is not in the context, say: "I am sorry, but this is outside my historical records."
    4. SAFETY: DO NOT answer questions about Physics (Flat Earth), Pop Culture, or Modern Events.
    
    USER QUESTION: {question}
    """

    # --- CALL GEMINI API (Your Existing Logic) ---
    raw_keys = os.getenv("GEMINI_API_KEY", "")
    if not raw_keys:
         return "Error: GEMINI_API_KEY not found."

    api_keys = [key.strip() for key in raw_keys.split(",") if key.strip()]
    last_error = ""
    
    for api_key in api_keys:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {"temperature": 0.0} 
        }
        
        try:
            data = json.dumps(payload).encode("utf-8")
            context = ssl._create_unverified_context()
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, context=context) as response:
                if response.getcode() == 200:
                    result = json.loads(response.read().decode("utf-8"))
                    return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            last_error = str(e)
            print(f"   Key failed. Switching keys...")
            continue
            
    return f"API Error: All keys failed. {last_error}"

if __name__ == "__main__":
    # Test cases
    print(f"Answer: {answer_question('Who are you?')}")
    print(f"Answer: {answer_question('Is the Earth flat?')}")