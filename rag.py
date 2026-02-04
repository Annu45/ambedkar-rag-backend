import os
import google.generativeai as genai

# Configure API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def answer_question(question):
    print(f"Asking Gemini Directly: {question}")
    
    try:
        # We use the Flash model which is faster and has a healthy quota
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # We give him a persona so he still acts like Dr. Ambedkar
        prompt = f"""
        You are Dr. B.R. Ambedkar. 
        You are speaking to a student.
        Answer the following question in the first person (using 'I').
        Keep your answer short, inspiring, and educational (max 3 sentences).
        
        Question: {question}
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"Error: {e}")
        return "My apologies, I am taking a moment to think. Please ask me again."