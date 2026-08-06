"""
semantic_search.py
Standalone semantic (vector) search over the Qdrant collection populated
by embed_and_index.py (using the gemini-embedding-001 model).
"""

import os
import google.generativeai as genai
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

_raw_key = os.getenv("GEMINI_API_KEY", "")
API_KEYS = [k.strip() for k in _raw_key.split(",") if k.strip()]

if not API_KEYS:
    raise RuntimeError("GEMINI_API_KEY is empty or not set in .env")

EMBED_MODEL = "models/gemini-embedding-001"  # must match embed_and_index.py


def embed_query(query: str):
    """Try each available Gemini key until one successfully embeds the query."""
    last_error = None
    for key in API_KEYS:
        try:
            genai.configure(api_key=key)
            result = genai.embed_content(
                model=EMBED_MODEL,
                content=query,
                task_type="retrieval_query",
            )
            return result["embedding"]
        except Exception as e:
            last_error = e
            print(f"  (key ending ...{key[-4:]} failed: {e}; trying next key)")
            continue
    raise RuntimeError(f"All API keys failed. Last error: {last_error}")


qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

COLLECTION_NAME = "ambedkar_speeches"


def semantic_search(query: str, top_k: int = 3):
    query_embedding = embed_query(query)

    response = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k,
    )
    results = response.points

    return [
        {
            "text": hit.payload.get("text", ""),
            "score": hit.score,
            "source": hit.payload.get("source"),
        }
        for hit in results
    ]


if __name__ == "__main__":
    question = input("Ask a question about Dr. Ambedkar: ")
    hits = semantic_search(question)

    print(f"\nTop {len(hits)} semantic matches:\n")
    for i, hit in enumerate(hits, start=1):
        print(f"[{i}] score={hit['score']:.4f}  source={hit['source']}")
        print(hit["text"][:300].replace("\n", " ") + "...\n")