import os
import google.generativeai as genai
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

# 1. Setup Google (The Brain)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Setup Qdrant (The Memory)
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

def answer_question(question: str):
    print(f"Thinking about: {question}")
    
    # 1. Convert question to vector (Using Google Cloud)
    # This is lightweight because it happens on Google's servers
    embedding_result = genai.embed_content(
        model="models/embedding-001",
        content=question,
        task_type="retrieval_query"
    )
    query_vector = embedding_result['embedding']

    # 2. Search Qdrant
    search_result = qdrant_client.search(
        collection_name="ambedkar_speeches",
        query_vector=query_vector,
        limit=3
    )

    # 3. Build Context
    context = "\n\n".join([hit.payload['text'] for hit in search_result])

    # 4. Ask Gemini
    prompt = f"""
    You are an expert on Dr. B.R. Ambedkar. Answer the question based ONLY on the context below.
    
    Context:
    {context}
    
    Question: {question}
    
    Answer:
    """
    
    response = model.generate_content(prompt)
    return response.text