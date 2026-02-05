import os
import json
import urllib.request
import ssl
from dotenv import load_dotenv

load_dotenv()

def answer_question(question):
    # Comma-separated keys ko list mein convert karein
    api_keys_raw = os.getenv("GEMINI_API_KEY", "")
    api_keys = [key.strip() for key in api_keys_raw.split(",") if key.strip()]
    
    if not api_keys:
        return "Error: No API keys found in environment variables."

    last_error = ""
    
    # Har key ko ek-ek karke try karein
    for api_key in api_keys:
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
                if response.getcode() == 200:
                    result = json.loads(response.read().decode("utf-8"))
                    return result['candidates'][0]['content']['parts'][0]['text']
                
        except Exception as e:
            last_error = str(e)
            print(f"Key failed, switching to next... Error: {last_error}")
            continue # Agli key par jump karein
            
    return f"All API keys exhausted or failed. Last error: {last_error}"

if __name__ == "__main__":
    print("Testing Multi-Key RAG Logic...")
    print(f"AI Response: {answer_question('Who are you?')}")