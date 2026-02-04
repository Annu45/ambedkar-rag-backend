from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from rag import answer_question
import uuid
import os
import threading
from gtts import gTTS  # ✅ CHANGED: Using gTTS instead of pyttsx3

print("API loaded")
load_dotenv()

app = FastAPI(
    title="Dr. Ambedkar RAG API",
    description="RAG-based QA system powered by Qdrant + Gemini",
    version="1.0"
)

# ✅ REQUIRED FOR RENDER (DO NOT REMOVE)
@app.get("/")
def health():
    return {"status": "API running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audio directory
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

class Query(BaseModel):
    question: str


# ✅ CLOUD-SAFE TTS (Uses Google Translate TTS instead of system drivers)
def text_to_speech_safe(text: str, file_path: str):
    try:
        # gTTS generates MP3 audio without needing sound card drivers
        tts = gTTS(text=text, lang='en')
        tts.save(file_path)
    except Exception as e:
        print("TTS failed:", e)


@app.post("/ask")
def ask_question(query: Query):
    answer = answer_question(query.question)

    # ✅ CHANGED: Using .mp3 which is smaller and standard for web
    audio_filename = f"{uuid.uuid4()}.mp3"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)

    # ✅ Run TTS in background thread (NON-BLOCKING)
    threading.Thread(
        target=text_to_speech_safe,
        args=(answer, audio_path),
        daemon=True
    ).start()

    return {
        "question": query.question,
        "answer": answer,
        "audio_url": f"/audio/{audio_filename}"
    }