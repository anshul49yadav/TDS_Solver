import google.generativeai as genai
from fastapi import FastAPI, Form, File, UploadFile
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

@app.post("/api/")
async def solve_question(
    question: str = Form(...), file: UploadFile = File(None)
):
    try:
        model_name = "gemini-1.5-pro-latest"  # Correct model name without 'models/' prefix
        model = genai.GenerativeModel(model_name)

        response = model.generate_content(question)
        return {"answer": response.text}

    except Exception as e:
        return {"error": str(e)}
