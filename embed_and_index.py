from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import json
import uuid

load_dotenv()

# ---------- Qdrant Client ----------
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60
)

COLLECTION_NAME = "ambedkar_rag"

# ---------- Embedding Model ----------
model = SentenceTransformer("all-MiniLM-L6-v2")

# ---------- Load Data ----------
with open("prepared_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

texts = [c["text"] for c in chunks]
print(f"Loaded {len(texts)} text chunks")

# ---------- Create Collection (if not exists) ----------
if COLLECTION_NAME not in [c.name for c in client.get_collections().collections]:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )
    print("Collection created")
else:
    print("Collection already exists")

# ---------- Generate Embeddings ----------
vectors = model.encode(texts, show_progress_bar=True).tolist()

# ---------- Prepare Points ----------
points = [
    PointStruct(
        id=str(uuid.uuid4()),   # safer than numeric IDs
        vector=vectors[i],
        payload=chunks[i]
    )
    for i in range(len(chunks))
]

# ---------- Upload to Qdrant ----------
client.upsert(
    collection_name=COLLECTION_NAME,
    points=points
)

print("✅ Vectors successfully uploaded to Qdrant")
