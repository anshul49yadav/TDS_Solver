from fastapi import FastAPI, Form, File, HTTPException
from typing import Optional
import google.generativeai as genai
import os
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()
GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

async def save_upload_file_temporarily(upload_file):
    try:
        temp_file_path = f"/tmp/{upload_file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await upload_file.read())
        return temp_file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="File could not be saved.")

async def get_gemini_response(prompt: str, file_path: Optional[str] = None) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")

        if file_path:
            with open(file_path, "rb") as f:
                response = model.generate_content([prompt, f.read()])
        else:
            response = model.generate_content([prompt])

        print(f"Generated answer from Gemini: {response.text}")
        return response.text
    except Exception as e:
        print(f"Error in get_gemini_response: {e}")
        raise HTTPException(status_code=500, detail="Error getting response from Gemini.")

@app.post("/api/")
async def process_question(
    question = Form(...),
    file = File(None)
):
    try:
        print(f"Received prompt: {question}")
        
        temp_file_path = None
        if file:
            print(f"File received: {file.filename}")
            temp_file_path = await save_upload_file_temporarily(file)
            print(f"File saved temporarily at: {temp_file_path}")

        answer = await get_gemini_response(question, temp_file_path)
        print(f"Generated answer: {answer}")
        return {"answer": answer}
    except Exception as e:
        print(f"Error in process_question: {e}")
        raise HTTPException(status_code=500, detail=str(e))
