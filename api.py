from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rag import answer_question
from gtts import gTTS
import os
import uuid

app = FastAPI()

# 1. ENABLE CORS (Allow Vercel to talk to Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all websites to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Setup Audio Directory
os.makedirs("audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

class Query(BaseModel):
    question: str

@app.get("/")
def home():
    return {"status": "Dr. Ambedkar API is Live"}

@app.post("/ask")
def ask_endpoint(query: Query):
    print(f"Received question: {query.question}")
    
    # 1. Get Text Answer from AI
    text_response = answer_question(query.question)
    
    # 2. Convert to Audio (Text-to-Speech)
    filename = f"{uuid.uuid4()}.mp3"
    filepath = f"audio/{filename}"
    tts = gTTS(text=text_response, lang='en')
    tts.save(filepath)
    
    # 3. Return Data
    return {
        "answer": text_response,
        "audio_url": f"/audio/{filename}"
    }