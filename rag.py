import os
import json
import time
import requests
from dotenv import load_dotenv

# --- LIBRARIES ---
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

load_dotenv()

# --- CONFIGURATION ---
DATA_FILE = "prepared_chunks.json"

# --- 1. INITIALIZE SEARCH (BM25) ---
print("⚙️ Initializing Keyword Search (BM25)...")

if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(f"CRITICAL ERROR: {DATA_FILE} not found!")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

documents = [Document(page_content=item.get("text", "")) for item in data if item]
retriever = BM25Retriever.from_documents(documents)
retriever.k = 3

print(f"✅ Search Engine Ready! Loaded {len(documents)} documents.")

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

# --- 3. ANSWER FUNCTION ---
def answer_question(question):
    print(f"\n🔍 Analyzing: {question}")
    
    # Search
    results = retriever.invoke(question)
    if not results:
        return "I am sorry, but I do not have information on this topic."

    context_text = "\n\n".join([doc.page_content for doc in results])
    
    prompt_text = f"""
    You are Dr. B. R. Ambedkar.
    CONTEXT: {context_text}
    
    STRICT RULES: 
    1. Answer ONLY using the provided CONTEXT. 
    2. If the User Question is about Physics (e.g. Flat Earth), Pop Culture, or Math, REFUSE to answer.
    3. Instead say: "I am sorry, but my knowledge is strictly limited to my life, the Constitution, and social reform."
    
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
                print(f"   ✅ Success!")
                return result['candidates'][0]['content']['parts'][0]['text']
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