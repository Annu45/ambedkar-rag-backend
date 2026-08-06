# LLM Ambedkar 🤖🕊️
**Dr. B. R. Ambedkar RAG Backend + 3D Talking Avatar**

LLM Ambedkar is a Retrieval-Augmented Generation (RAG) chatbot that answers questions in the voice and persona of Dr. B. R. Ambedkar, grounded in his actual speeches and essays. It's served through a FastAPI backend and a Three.js-based web frontend with a 3D avatar.

Part of a DIAT internship project under the supervision of Prof. CRS Kumar.

**Live demo:** https://ambedkar-rag-backend.vercel.app/

---

## 🚀 Features

- 📚 Context-grounded answers using **BM25 keyword retrieval** over Ambedkar's speeches and essays
- 🧠 Persona-scoped generation via Google Gemini, with prompt-level guardrails that keep answers on-topic (Constitution, law, caste, his life) and refuse unrelated questions
- 🔑 Multi-key API fallback with dynamic model discovery and 429 rate-limit handling
- 🗣️ Two text-to-speech paths: server-side audio generation (gTTS) and, on the web frontend, the browser's built-in Web Speech API (see [Known gaps](#-known-gaps--roadmap))
- 📝 Interaction logging to MongoDB (question, answer, timestamp)
- 🌐 REST API via FastAPI, with Swagger docs at `/docs`
- 🎮 3D avatar (Three.js + GLTF/DRACO) that animates while speaking
- 🧩 Hybrid retrieval: **BM25 keyword search is primary**, with a verified Qdrant + Gemini-embeddings semantic search as an automatic fallback if BM25 returns nothing

---

## 🏗️ Architecture (as currently deployed)

```
Frontend (Three.js avatar, hosted separately)
        │  POST /ask  { question }
        ▼
FastAPI (api.py)
        │
        ▼
rag.py → BM25Retriever over prepared_chunks.json (top-3 chunks, primary)
        │  (falls back to Qdrant semantic search only if BM25 returns nothing)
        ▼
Persona prompt + retrieved context → Gemini generateContent
        │
        ├──► MongoDB (logs question/answer/timestamp, if configured)
        └──► gTTS → .wav/.mp3 saved to /audio, URL returned in response
        │
        ▼
JSON response { answer, audio_url } → frontend
        │
        ▼
Browser speaks the answer via Web Speech API and animates the avatar
```

**Retrieval note:** the live `/ask` endpoint uses **BM25** (sparse/keyword search) as the primary retrieval method — chosen because its answers tested more useful for this corpus. A verified semantic-search path (`embed_and_index.py` embeds every chunk with Gemini's `gemini-embedding-001` model, 3072-dim, into a Qdrant collection) is wired into `rag.py` as an **automatic fallback**, used only if BM25 returns no results. In practice BM25 almost always returns its top-k regardless of relevance score, so the fallback rarely triggers — it exists as a safety net rather than the everyday path. `semantic_search.py` remains available as a standalone script for testing the Qdrant path directly. See [Known gaps](#-known-gaps--roadmap).

---

## 📁 Project Structure

```
Dr.Ambedkar-Rag/
│
├── api.py                 # FastAPI server — /ask endpoint, TTS, CORS, static audio hosting
├── rag.py                 # Live RAG logic: BM25 (primary) + Qdrant semantic search (fallback) + Gemini generation + Mongo logging
├── chunks.py               # Splits data/ text files into overlapping chunks → prepared_chunks.json
├── create_qdrant_db.py     # Legacy/superseded — embed_and_index.py now creates its own collection
├── embed_and_index.py      # Embeds chunks with gemini-embedding-001 (3072-dim) and uploads to Qdrant
├── semantic_search.py      # Standalone, verified semantic search over the Qdrant collection
├── list_embedding_models.py # Utility: lists embedding-capable Gemini models for your API key
├── list_models_stable.py   # Utility: lists Gemini chat models available to your API key
├── check_models.py         # Utility: brute-force tests known Gemini model names against your key
├── data/                   # Source .txt files — Ambedkar's speeches and essays
├── data_manifest.json      # Per-file metadata (author, year, category) used during chunking
├── prepared_chunks.json    # Output of chunks.py — what rag.py actually loads at runtime
├── requirements.txt        # Python dependencies
├── vercel.json             # Optional serverless deployment config (not the currently live deployment)
├── audio/                  # Generated speech files (created at runtime)
├── frontend/                # Three.js web client + 3D avatar model
└── .env                    # API keys and connection strings (not committed)
```

---

## ⚙️ Installation

Create and activate a virtual environment:

```bash
python -m venv env
env\Scripts\activate      # Windows
source env/bin/activate   # macOS/Linux
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 🔑 Set API Keys

Create a `.env` file in the root directory:

```
GEMINI_API_KEY=YOUR_GEMINI_API_KEY        # comma-separate multiple keys for automatic fallback
MONGO_URI=YOUR_MONGODB_CONNECTION_STRING  # optional — logging is skipped if unset

# Only needed if you're using the optional vector-search pipeline below
QDRANT_URL=YOUR_QDRANT_URL
QDRANT_API_KEY=YOUR_QDRANT_API_KEY
```

## 🧩 Prepare the Retrieval Data (run once)

```bash
python chunks.py
```

This reads every file in `data/`, splits it into overlapping 400-word chunks (100-word overlap), attaches metadata from `data_manifest.json`, and writes `prepared_chunks.json` — the file `rag.py` loads at startup for BM25 retrieval. This is the only data-prep step required for the app to run.

### Optional: build and query the vector-search pipeline

These scripts build and let you directly test the semantic-search side of the hybrid retrieval used in `rag.py`:

```bash
python list_embedding_models.py  # confirms which embedding model your API key supports
python embed_and_index.py        # embeds all chunks with gemini-embedding-001 (3072-dim) and (re)creates
                                  # the "ambedkar_speeches" Qdrant collection — takes ~45 min (274 chunks,
                                  # rate-limited to one request per ~10s)
python semantic_search.py        # queries that collection — prompts for a question, prints top-3
                                  # matches with similarity scores
```

⚠️ `create_qdrant_db.py` is now legacy — `embed_and_index.py` creates/recreates its own collection, so `create_qdrant_db.py`'s separate 384-dim collection is unused. Safe to remove once confirmed.

Note: Google retired the older `embedding-001` model; `embed_and_index.py` and `semantic_search.py` both use its replacement, `gemini-embedding-001`, and must stay in sync on model name and vector size if either changes.

## ▶️ Run the Backend

```bash
uvicorn api:app --reload
```

Backend runs at `http://127.0.0.1:8000`. On startup you should see BM25 initialization logs and `Uvicorn running on http://127.0.0.1:8000`.

## 🧪 API Testing (Thunder Client / Postman)

**Endpoint:** `POST http://127.0.0.1:8000/ask`

**Headers:** `Content-Type: application/json`

**Body:**
```json
{
  "question": "Who was Dr. B. R. Ambedkar?"
}
```

**Response:**
```json
{
  "answer": "Dr. B. R. Ambedkar was a social reformer...",
  "audio_url": "/audio/abcd1234.mp3"
}
```

`audio_url` is a gTTS-generated file served from the backend; the current web frontend does not play it (see below) but it's available for other clients (e.g. an Unreal Engine integration).

## 🌐 API Documentation

Swagger UI: `http://127.0.0.1:8000/docs`

## 🖥️ Frontend

The `frontend/` folder is a static Three.js app (no build step). It:
- Loads a `.glb` 3D model of Dr. Ambedkar and animates a "talking" clip while speech is playing
- Prompts for a username on first load (stored in `sessionStorage`) and tags it onto each question sent to the backend
- Fetches from the live API at `https://ambedkar-api.onrender.com/ask` (hardcoded in `script.js`) — update this if you deploy your own backend
- Uses the **browser's Web Speech API** to speak answers aloud (not the backend's gTTS audio)

---

## 📌 Known gaps / roadmap

- **Retrieval:** BM25 is primary and Qdrant is wired in as a fallback, but since BM25 rarely returns empty, the fallback is mostly untested under real traffic — worth deliberately triggering it (e.g. an empty-corpus test) to confirm it behaves as expected.
- **Audio:** wire the frontend to play the backend's `audio_url` (or drop gTTS server-side generation if the Web Speech API path is the intended long-term approach) so there's a single source of truth for speech.
- **Deployment:** the site (frontend) is deployed on Vercel at [ambedkar-rag-backend.vercel.app](https://ambedkar-rag-backend.vercel.app/), while the API backend runs separately on Render. `vercel.json` still configures `api.py` to also run as a Vercel serverless function — this was likely an earlier attempt to host the backend on Vercel too, probably moved to Render because Vercel's serverless functions have an ephemeral filesystem, which doesn't suit writing and re-serving generated `.mp3` files from `audio/`. Worth removing `vercel.json` if it's confirmed unused, to avoid confusing future readers.

---

## ✨ Pipeline Summary

```
User Question
   ↓
FastAPI (/ask)
   ↓
BM25 retrieval over prepared_chunks.json (primary; Qdrant semantic search as fallback)
   ↓
Gemini generation (persona-scoped prompt, multi-key fallback)
   ↓
MongoDB logging (if configured) + gTTS audio generation
   ↓
JSON response → Frontend speaks via Web Speech API, avatar animates
```