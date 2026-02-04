import os
import json
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

load_dotenv()

# Setup Keys
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

collection_name = "ambedkar_speeches"

# 1. Re-create Collection (Google Embeddings are size 768, not 384)
client.recreate_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
)
print("Collection Reset!")

# 2. Load Chunks
with open("prepared_chunks.json", "r") as f:
    chunks = json.load(f)

print(f"Uploading {len(chunks)} chunks...")

# 3. Embed and Upload
chunk_texts = [c['text'] for c in chunks]

# Get embeddings in batch from Google
# Note: Google has a limit, so we might need to batch if you have thousands.
# For <1000 chunks, this loop is fine.
vectors = []
for text in chunk_texts:
    emb = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    vectors.append(emb['embedding'])
    print(".", end="", flush=True)

# 4. Upload to Qdrant
client.upload_collection(
    collection_name=collection_name,
    vectors=vectors,
    payload=chunks
)

print("\n✅ Success! Data re-uploaded with Cloud Embeddings.")