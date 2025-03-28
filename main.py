import os
# import logging
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

# Import the intelligent routing logic
from intelligent_assignment_router import process_assignment_question

# # Configure logging
# def setup_logging():
#     # Create logs directory if it doesn't exist
#     log_dir = 'logs'
#     os.makedirs(log_dir, exist_ok=True)

#     # Configure logging to write to both console and file
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#         handlers=[
#             # Log to console
#             logging.StreamHandler(),
#             # Log to file
#             logging.FileHandler(os.path.join(log_dir, 'assignment_processor.log'), encoding='utf-8')
#         ]
#     )

# # Create logger
# logger = logging.getLogger(__name__)

# # Setup logging
# setup_logging()

app = FastAPI(title="Intelligent Assignment Question Processor")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/")
async def process_assignment(
    question: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    # Log the incoming request details
    print(f"Received assignment processing request")
    print(f"Question length: {len(question)} characters")
    print(f"File provided: {file.filename if file else 'No file'}")

    try:
        # Create temp directory if it doesn't exist
        temp_dir = '/tmp'
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save file temporarily if provided
        temp_file_path = None
        if file:
            file_extension = os.path.splitext(file.filename)[1]
            temp_file_path = os.path.join(temp_dir, f"temp_{os.urandom(8).hex()}{file_extension}")
            
            # Save file and log file details
            print(f"Saving temporary file: {temp_file_path}")
            with open(temp_file_path, 'wb') as buffer:
                file_content = await file.read()
                buffer.write(file_content)
                print(f"Temporary file saved. Size: {len(file_content)} bytes")
        
        # Process the assignment question using intelligent routing
        print("Starting assignment question processing")
        result = process_assignment_question(
            question=question, 
            file_path=temp_file_path
        )
        print("Assignment question processing completed successfully")
        
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            print(f"Removing temporary file: {temp_file_path}")
            os.unlink(temp_file_path)
        
        return result
    
    except Exception as e:
        # Log the exception with full details
        print(f"Error processing assignment: {str(e)}", exc_info=True)
        
        # Clean up temporary file if it exists
        if temp_file_path and os.path.exists(temp_file_path): 
            print(f"Removing temporary file due to error: {temp_file_path}")
            os.unlink(temp_file_path)
        
        # Raise HTTP exception with error details
        raise HTTPException(status_code=500, detail=str(e))

# Add startup and shutdown event logging
@app.on_event("startup")
async def startup_event():
    print("Application starting up")

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutting down")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)