import google.generativeai as genai
from fastapi import FastAPI, Form, File, UploadFile
import os
import zipfile
import ujson
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure API key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Helper function to extract data from CSV using ujson
def extract_csv_data(zip_file_path):
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall("temp_folder")
            for file_name in zip_ref.namelist():
                if file_name.endswith(".csv"):
                    with open(f"temp_folder/{file_name}", 'r', encoding='utf-8') as f:
                        headers = f.readline().strip().split(',')
                        if 'answer' in headers:
                            answer_index = headers.index('answer')
                            # Read the first row
                            first_row = f.readline().strip().split(',')
                            return str(first_row[answer_index])
        return "No answer column found."
    except Exception as e:
        return str(e)

# API Endpoint
@app.post("/api/")
async def solve_question(
    question: str = Form(...), 
    file: UploadFile = File(None)
):
    try:
        # If file is provided, extract and find answer
        if file:
            file_location = f"temp_folder/{file.filename}"
            os.makedirs("temp_folder", exist_ok=True)
            with open(file_location, "wb") as f:
                f.write(await file.read())
            answer = extract_csv_data(file_location)
            return {"answer": answer}

        # If no file is provided, use Gemini AI for response
        model_name = "gemini-1.5-pro-latest"
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(question)
        return {"answer": response.text}

    except Exception as e:
        return {"error": str(e)}
