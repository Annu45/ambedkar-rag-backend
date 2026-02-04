import os
import google.generativeai as genai

# Configure API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def answer_question(question):
    print(f"Asking Gemini: {question}")
    
    # 1. Try the newest, fastest model first
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(question)
        return response.text.strip()
    except Exception as e1:
        print(f"Flash failed ({e1}). Trying Pro...")
        
        # 2. If Flash fails, try the standard model
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(question)
            return response.text.strip()
        except Exception as e2:
            print(f"All models failed. Error: {e2}")
            return "My apologies, I am having trouble connecting to Google right now. Please ask again."