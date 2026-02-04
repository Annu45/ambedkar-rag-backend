import os
import json
from pathlib import Path

# ---------------- CONFIG ----------------
DATA_DIR = "data"
MANIFEST_FILE = "data_manifest.json"
CHUNK_SIZE = 400       # words
OVERLAP = 100          # words
# ----------------------------------------

def load_manifest(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_text(text):
    text = text.replace("\r", "\n")
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
    return text

def chunk_text(text, size=400, overlap=100):
    words = text.split()
    chunks = []

    start = 0
    chunk_id = 0

    while start < len(words):
        end = start + size
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        chunks.append({
            "chunk_id": chunk_id,
            "text": chunk_text,
            "start_word": start,
            "end_word": end
        })

        chunk_id += 1
        start += size - overlap

    return chunks

def process_files():
    manifest = load_manifest(MANIFEST_FILE)
    all_chunks = []

    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.startswith(".") or not file.lower().endswith(".txt"):
                continue

            meta = manifest.get(file)
            if meta is None:
                print(f"[WARN] Metadata missing for {file}, using defaults")
                meta = {
                    "author": "B. R. Ambedkar",
                    "year": "unknown",
                    "category": "unknown"
                }

            file_path = Path(root) / file
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()

            cleaned = clean_text(raw_text)
            chunks = chunk_text(cleaned)

            for c in chunks:
                chunk_record = {
                    "text": c["text"],
                    "metadata": {
                        "source": file,
                        "author": meta["author"],
                        "year": meta["year"],
                        "category": meta["category"],
                        "chunk_id": c["chunk_id"],
                        "start_word": c["start_word"],
                        "end_word": c["end_word"]
                    }
                }
                all_chunks.append(chunk_record)

    return all_chunks

if __name__ == "__main__":

    chunks = process_files()
    print(f"Prepared {len(chunks)} chunks.")

    # Optional: save for inspection
    with open("prepared_chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)