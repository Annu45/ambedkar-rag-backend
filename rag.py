import certifi
import os
import json
import time
import requests
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient

# --- LIBRARIES ---
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
import google.generativeai as genai
from qdrant_client import QdrantClient

load_dotenv()

# --- MONGODB SETUP ---
MONGO_URI = os.getenv("MONGO_URI")
chat_collection = None

if MONGO_URI:
    try:
        # We add tlsCAFile=certifi.where() to fix the SSL handshake error!
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["ambedkar_ai"] 
        chat_collection = db["interactions"] 
        print("✅ Successfully connected to MongoDB!")
    except Exception as e:
        print(f"⚠️ MongoDB Connection Error: {e}")

# --- CONFIGURATION ---
DATA_FILE = "prepared_chunks.json"

# --- 1. INITIALIZE SEARCH (BM25) — this is the primary retrieval method ---
print("⚙️ Initializing Keyword Search (BM25)...")

if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(f"CRITICAL ERROR: {DATA_FILE} not found!")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

documents = [Document(page_content=item.get("text", "")) for item in data if item]
retriever = BM25Retriever.from_documents(documents)
retriever.k = 3

print(f"✅ Search Engine Ready! Loaded {len(documents)} documents.")

# --- 1b. INITIALIZE SEMANTIC SEARCH (Qdrant) — fallback only, used if BM25 finds nothing ---
GEMINI_API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEY", "").split(",") if k.strip()]
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = "ambedkar_speeches"
EMBED_MODEL = "models/gemini-embedding-001"

qdrant_client = None
if QDRANT_URL and QDRANT_API_KEY:
    try:
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=5)
        print("✅ Qdrant client connected — semantic search available as fallback.")
    except Exception as e:
        print(f"⚠️ Qdrant connection failed, no fallback available: {e}")
        qdrant_client = None
else:
    print("ℹ️ QDRANT_URL/QDRANT_API_KEY not set — BM25 only, no fallback.")


def embed_query_for_retrieval(question):
    """Try each available Gemini key to embed the query. Returns None on total failure."""
    for key in GEMINI_API_KEYS:
        try:
            genai.configure(api_key=key)
            result = genai.embed_content(
                model=EMBED_MODEL,
                content=question,
                task_type="retrieval_query",
            )
            return result["embedding"]
        except Exception:
            continue
    return None


def semantic_retrieve(question, top_k=3):
    """Qdrant semantic search — only called when BM25 returns nothing. Returns a list of
    matched texts, or None if unavailable/failed."""
    if qdrant_client is None:
        return None
    try:
        query_embedding = embed_query_for_retrieval(question)
        if query_embedding is None:
            return None

        response = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_embedding,
            limit=top_k,
        )
        hits = response.points
        texts = [hit.payload.get("text", "") for hit in hits if hit.payload.get("text")]
        return texts if texts else None
    except Exception as e:
        print(f"   ⚠️ Semantic fallback also failed ({e}).")
        return None

# --- 2. DYNAMIC MODEL FINDER ---
def get_available_model(api_key):
    """Asks Google which models are actually enabled for this key."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Look for any model that supports 'generateContent'
            for model in data.get('models', []):
                if "generateContent" in model.get('supportedGenerationMethods', []):
                    # Prefer 'gemini' models over 'paired' models
                    if "gemini" in model['name']:
                        return model['name'] # Returns full name e.g. "models/gemini-pro"
            return "models/gemini-pro" # Fallback
        else:
            print(f"   ⚠️ Could not list models: {response.status_code}")
            return "models/gemini-pro"
    except Exception as e:
        print(f"   ⚠️ Network error listing models: {e}")
        return "models/gemini-pro"

# --- UPDATED ANSWER FUNCTION ---
def answer_question(question):
    print(f"\n🔍 Analyzing: {question}")

    # --- HYBRID RETRIEVAL: BM25 first (primary), Qdrant semantic search only as fallback ---
    results = retriever.invoke(question)
    if results:
        print("   🔎 Retrieval: BM25 keyword search")
        context_text = "\n\n".join([doc.page_content for doc in results])
    else:
        print("   🔎 BM25 found nothing — trying Qdrant semantic search (fallback)")
        semantic_results = semantic_retrieve(question)
        if semantic_results:
            print("   🔎 Retrieval: Qdrant semantic search (fallback)")
            context_text = "\n\n".join(semantic_results)
        else:
            print("   🔎 Retrieval: no results from either method")
            context_text = "No specific documents found."

    prompt_text = f"""
    You are Dr. B. R. Ambedkar, the architect of the Indian Constitution.
    
    PRIMARY CONTEXT: {context_text}
    
    STRICT OPERATING PROCEDURES: 
    1. If the User Question is about the Indian Constitution, Law, Caste, or your life (e.g., Article 370), 
       answer with historical accuracy. If the PRIMARY CONTEXT is missing details, use your known 
       historical stance but remain professional and scholarly.
    2. If the User Question is about Modern Technology (iPhones), Science/Physics (Flat Earth), 
       Pop Culture, or Math, you MUST REFUSE.
    3. In case of refusal, say: "I am sorry, but my knowledge is strictly limited to my life, 
       the Indian Constitution, and social reform."
    
    USER QUESTION: {question}
    """


    # Get Keys
    raw_keys = os.getenv("GEMINI_API_KEY", "")
    api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    
    if not api_keys:
        return "Error: GEMINI_API_KEY not found."

    # Try keys until one works
    for i, api_key in enumerate(api_keys):
        # DYNAMICALLY FIND A WORKING MODEL
        model_name = get_available_model(api_key)
        # Remove 'models/' prefix if present for the URL construction below
        clean_model_name = model_name.replace("models/", "")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": api_key}
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

        try:
            print(f"   🔄 Key {i+1}: Trying model '{clean_model_name}'...")
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                final_answer = result['candidates'][0]['content']['parts'][0]['text']
                
                # --- SAVE TO MONGODB ---
                if chat_collection is not None:
                    try:
                        chat_collection.insert_one({
                            "question": question,
                            "answer": final_answer,
                            "timestamp": datetime.utcnow()
                        })
                        print("   📝 Interaction logged to database.")
                    except Exception as e:
                        print(f"   ⚠️ Failed to log interaction: {e}")
                # -----------------------

                print(f"   ✅ Success!")
                return final_answer
                
            elif response.status_code == 429:
                print("   ⏳ Rate Limit. Waiting 2s...")
                time.sleep(2)
                continue
            else:
                print(f"   ❌ Failed ({response.status_code}): {response.text[:50]}...")
                continue

        except Exception as e:
            print(f"   ⚠️ Connection Error: {str(e)}")
            continue

    return "API Error: Unable to connect to Google AI. Please check API keys."

if __name__ == "__main__":
    print(f"Answer: {answer_question('Who are you?')}")