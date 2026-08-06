"""
list_embedding_models.py
Lists which embedding-capable models are available for your Gemini API key.
Run this to find the correct model name to use in semantic_search.py and
embed_and_index.py, since "models/embedding-001" may have been deprecated.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

raw_key = os.getenv("GEMINI_API_KEY", "")
keys = [k.strip() for k in raw_key.split(",") if k.strip()]

if not keys:
    print("No GEMINI_API_KEY found in .env")
else:
    genai.configure(api_key=keys[0])
    print(f"Checking embedding models available for key ...{keys[0][-6:]}\n")
    try:
        found = False
        for m in genai.list_models():
            if "embedContent" in m.supported_generation_methods:
                print(f"AVAILABLE FOR EMBEDDING: {m.name}")
                found = True
        if not found:
            print("No embedding-capable models found for this key.")
    except Exception as e:
        print(f"Error: {e}")