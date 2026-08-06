import os
import json
import time
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

load_dotenv()

# Setup Keys
genai.configure(api_key=os.getenv("GEMINI_API_KEY").split(",")[0].strip())
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

collection_name = "ambedkar_speeches"
EMBED_MODEL = "models/gemini-embedding-001"  # updated: embedding-001 was retired
VECTOR_SIZE = 3072  # gemini-embedding-001's default output dimension

# 1. Reset Database
print("Checking database...")
client.recreate_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
)
print("Database reset. Starting Super Safe Upload (This will take ~45 mins)...")

# 2. Load Data
with open("prepared_chunks.json", "r") as f:
    chunks = json.load(f)

# 3. Upload Loop
vectors = []
batch_size = 50

for i, chunk in enumerate(chunks):
    success = False
    while not success:
        try:
            # Get Vector from Google
            emb = genai.embed_content(
                model=EMBED_MODEL,
                content=chunk['text'],
                task_type="retrieval_document"
            )
            vectors.append(emb['embedding'])
            success = True

            # Progress bar
            print(f"Processed {i+1}/{len(chunks)}")

            # MANDATORY SLEEP: 10 Seconds to be 100% safe
            time.sleep(10)

        except Exception as e:
            print(f"\n⚠️ Rate Limit Hit. Waiting 2 minutes to cool down... ({e})")
            time.sleep(120)  # Wait 2 minutes if it fails

    # Upload batch to Qdrant every 50 items
    if len(vectors) >= batch_size:
        try:
            client.upload_collection(
                collection_name=collection_name,
                vectors=vectors,
                payload=chunks[i-(batch_size-1):i+1]
            )
            vectors = []  # Clear batch
            print(f"--> Uploaded batch to Cloud")
        except Exception as e:
            print(f"Upload failed: {e}")

# Upload remaining
if vectors:
    client.upload_collection(
        collection_name=collection_name,
        vectors=vectors,
        payload=chunks[-len(vectors):]
    )

print("\n✅ Success! All data uploaded to Qdrant Cloud.")