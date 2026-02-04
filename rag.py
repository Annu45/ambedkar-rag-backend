import os
import json
import urllib.request

def answer_question(question):
    print(f"Asking Gemini (Direct REST): {question}")
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return "Error: API Key is missing."

    # We use the raw API URL directly to bypass the broken library
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    # Dr. Ambedkar Persona
    prompt_text = f"""
    You are Dr. B.R. Ambedkar.
    You are speaking to a student.
    Answer this question in the first person (using 'I').
    Keep it short (max 3 sentences) and inspiring.
    
    Question: {question}
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    try:
        # Send the message directly to Google
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            # Extract the answer
            return result['candidates'][0]['content']['parts'][0]['text']
            
    except Exception as e:
        print(f"REST API Error: {e}")
        return "My apologies, I am having trouble connecting. Please check the Render Logs."