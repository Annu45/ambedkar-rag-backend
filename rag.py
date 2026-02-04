from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import google.generativeai as genai  # <--- USING STABLE LIBRARY
from dotenv import load_dotenv
import os

load_dotenv()
print("RAG loaded - Stable Mode")

# ---------- 1. Configure Google Gemini (Stable) ----------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("⚠️ CRITICAL: GEMINI_API_KEY is missing in .env")
else:
    genai.configure(api_key=api_key)

# ---------- 2. Configure Qdrant ----------
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_key = os.getenv("QDRANT_API_KEY", None)

try:
    qdrant = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_key,
        timeout=10
    )
except Exception as e:
    print(f"⚠️ Qdrant Init Error: {e}")

# ---------- 3. Embedding Model ----------
embedder = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME = "ambedkar_rag"

def retrieve(query, top_k=3):
    try:
        vector = embedder.encode(query).tolist()
        
        # Robust query using query_points
        search_result = qdrant.query_points(
            collection_name=COLLECTION_NAME, 
            query=vector,
            limit=top_k,
            with_payload=True
        )
        
        # Handle formats
        if hasattr(search_result, 'points'):
            results = search_result.points
        else:
            results = search_result
            
        return [p.payload for p in results]
        
    except Exception as e:
        print(f"❌ Retrieval Error: {e}")
        return [f"System Error: {str(e)}"]

def answer_question(question):
    # Check Key
    if not api_key:
        return "Error: GEMINI_API_KEY is missing."

    # Retrieve
    try:
        contexts = retrieve(question, top_k=3)
    except Exception as e:
        return f"Database Error: {e}"

    if not contexts:
        return "No relevant context found."
    
    if isinstance(contexts[0], str) and "System Error" in contexts[0]:
        return f"Database Failed: {contexts[0]}"

    context_text = "\n\n".join(
        f"Source: {c.get('source', 'Unknown')}\nText: {c.get('text', '')}"
        for c in contexts if isinstance(c, dict)
    )

    prompt = f"""
    You are a scholarly assistant.
    Context: {context_text}
    Question: {question}
    """

   
# Generate Answer using STABLE library
    try:
        
        model = genai.GenerativeModel('models/gemini-flash-latest') 
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Google Error: {e}"