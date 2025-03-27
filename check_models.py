import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

def list_models():
    try:
        models = genai.list_models()
        print("Available Models:")
        for model in models:
            print(f"Model Name: {model.name}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    list_models()
