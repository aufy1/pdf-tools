import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from logic import process_pdf_translation
from converters import convert_pdf_to_word

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = "/data/outputs"
UPLOAD_DIR = "/app/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "Backend is running", "service": "BabelDOC AI Translator"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "status": "uploaded"}

@app.post("/translate/{filename}")
async def translate_document(filename: str):
    input_path = os.path.join(UPLOAD_DIR, filename)
    output_filename = f"UA_{filename}"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        process_pdf_translation(input_path, output_path, source_lang='PL', target_lang='UK')
        
        return {
            "status": "completed", 
            "original": filename, 
            "translated": output_filename,
            "download_url": f"/downloads/{output_filename}" 
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/convert/to-word/{filename}")
async def convert_document_to_word(filename: str):
    input_path = os.path.join(UPLOAD_DIR, filename)
    base_name = os.path.splitext(filename)[0]
    output_filename = f"{base_name}.docx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        convert_pdf_to_word(input_path, output_path)
        return {
            "status": "completed", 
            "original": filename, 
            "converted": output_filename,
            "download_url": f"/downloads/{output_filename}" 
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))