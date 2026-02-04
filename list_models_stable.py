import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY is missing.")
else:
    genai.configure(api_key=api_key)
    
    print("Checking available models for your key...")
    try:
        count = 0
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ AVAILABLE: {m.name}")
                count += 1
        
        if count == 0:
            print("⚠️ No chat models found. Check if 'Generative Language API' is enabled in Google Cloud Console.")
            
    except Exception as e:
        print(f"❌ Error: {e}")