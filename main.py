import os
from typing import Optional
import zipfile

from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

app = FastAPI()

async def extract_files_from_zip(zip_path: str):
    """
    Extract files from a zip archive for serverless environment.
    
    Args:
        zip_path (str): Path to the zip file
    
    Returns:
        List of tuples containing filename and file content
    """
    try:
        extracted_files = []
        # Ensure /tmp directory exists and is writable
        os.makedirs('/tmp/extracted', exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("/tmp/extracted")
            
            for file_name in zip_ref.namelist():
                # Skip directories and hidden files
                if not file_name.startswith('.') and not file_name.endswith('/'):
                    file_path = f"/tmp/extracted/{file_name}"
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            extracted_files.append((file_name, content))
                    except UnicodeDecodeError:
                        # Handle potential binary or non-UTF-8 files
                        continue
        
        return extracted_files
    except Exception as e:
        print(f"Error extracting files from zip: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid zip file: {str(e)}")

async def save_upload_file_temporarily(upload_file: UploadFile):
    """
    Save uploaded file to /tmp directory.
    
    Args:
        upload_file (UploadFile): Uploaded file
    
    Returns:
        str: Path to the saved file
    """
    try:
        # Ensure /tmp directory exists
        os.makedirs('/tmp', exist_ok=True)
        
        # Generate a unique filename
        temp_file_path = f"/tmp/{upload_file.filename}"
        
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await upload_file.read())
        
        return temp_file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="File could not be saved.")

async def get_gemini_response(prompt: str, file_path: Optional[str] = None) -> str:
    """
    Generate response from Gemini with context handling.
    
    Args:
        prompt (str): User's question
        file_path (Optional[str]): Path to uploaded zip file
    
    Returns:
        str: Generated response
    """
    try:
        # Use the latest Gemini Pro model
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        
        # Construct context-aware prompt
        if file_path:
            extracted_files = await extract_files_from_zip(file_path)
            
            # Construct a more structured context
            context = "Context Files:\n" + "\n".join([
                f"File: {name}\n---\n{content[:1000]}..." 
                for name, content in extracted_files
            ])
            
            full_prompt = f"""
            Task: Carefully analyze the provided context and answer the question precisely.

            Question: {prompt}

            {context}

            Instructions:
            - Provide a clear, concise answer
            - Reference specific files or contexts if relevant
            - If the context doesn't contain enough information, state that clearly
            """
        else:
            full_prompt = prompt
        
        # Generate response with safety settings
        generation_config = genai.types.GenerationConfig(
            temperature=0.2,  # More focused response
            max_output_tokens=2048  # Limit response length
        )
        
        response = model.generate_content(
            full_prompt, 
            generation_config=generation_config
        )
        
        return response.text.strip()
    
    except Exception as e:
        print(f"Gemini response generation error: {e}")
        raise HTTPException(status_code=500, detail="Error processing request")

@app.post("/api/")
async def process_question(
    question: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """
    Process user question with optional file upload.
    
    Args:
        question (str): User's question
        file (Optional[UploadFile]): Uploaded zip file
    
    Returns:
        dict: Response from Gemini
    """
    try:
        # Validate inputs
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        temp_file_path = None
        if file:
            # Save file to /tmp
            temp_file_path = await save_upload_file_temporarily(file)
        
        answer = await get_gemini_response(question, temp_file_path)
        
        # Clean up temporary file if it exists
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        # Clean up extracted files directory
        if os.path.exists("/tmp/extracted"):
            import shutil
            shutil.rmtree("/tmp/extracted", ignore_errors=True)
        
        return {"answer": answer}
    
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)