import os
import json
import urllib.request
import ssl
from dotenv import load_dotenv

load_dotenv()

def answer_question(question):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    
    # MATCHING YOUR LIST: Using gemini-2.5-flash on the v1beta endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{
            "parts": [{"text": f"You are Dr. B.R. Ambedkar. Answer shortly: {question}"}]
        }]
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        context = ssl._create_unverified_context()
        
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=context) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result['candidates'][0]['content']['parts'][0]['text']
            
    except Exception as e:
        return f"Final Connection Error: {e}"

if __name__ == "__main__":
    print("Testing with the verified model: gemini-2.5-flash...")
    print(f"AI Response: {answer_question('Who are you?')}")