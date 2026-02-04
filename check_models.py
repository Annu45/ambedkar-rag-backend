import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# List of likely model names to try
candidates = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-pro-001",
    "gemini-pro",
    "gemini-1.0-pro",
    "gemini-2.0-flash-exp"
]

print("🚀 Starting Brute Force Model Test...\n")

found_working = False

for model_name in candidates:
    print(f"👉 Testing: {model_name} ... ", end="")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Hello, just say 'Working'."
        )
        print("✅ SUCCESS!")
        print(f"\n🎉 WINNER: You should use '{model_name}' in rag.py\n")
        found_working = True
        break  # Stop after finding the first working one
    except Exception as e:
        # Check if it's a 404 (Not Found) or something else
        if "404" in str(e) or "NOT_FOUND" in str(e):
            print("❌ Not Found")
        else:
            print(f"❌ Error: {e}")

if not found_working:
    print("\n⚠️ None of the common model names worked. Please check your API key permissions.")