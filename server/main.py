import os
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from logic import process_pdf_translation

app = FastAPI()

# CORS settings...
origins = ["*"] # Dla uproszczenia w dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ZMIANA: Zapisujemy pliki poza folderem aplikacji (/app)
OUTPUT_DIR = "/data/outputs"  
UPLOAD_DIR = "/app/uploads"   # Uploady tymczasowe mogą zostać w /app

# Upewniamy się, że foldery istnieją
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "Backend is running", "service": "PDF Translator AI"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "status": "uploaded"}

@app.post("/translate/{filename}")
async def translate_document(filename: str, background_tasks: BackgroundTasks):
    input_path = os.path.join(UPLOAD_DIR, filename)
    output_filename = f"UA_{filename}"
    
    # Ścieżka docelowa w nowym folderze /data/outputs
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Uruchamiamy logikę tłumaczenia
        process_pdf_translation(input_path, output_path)
        
        return {
            "status": "completed", 
            "original": filename, 
            "translated": output_filename,
            # Link dla Nginx pozostaje ten sam (bo Nginx mapuje ten sam folder ./outputs)
            "download_url": f"/downloads/{output_filename}" 
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/convert/to-word/{filename}")
async def convert_document_to_word(filename: str):
    input_path = os.path.join(UPLOAD_DIR, filename)
    
    # Zmiana rozszerzenia pliku wyjściowego na .docx
    base_name = os.path.splitext(filename)[0]
    output_filename = f"{base_name}.docx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File not found. Please upload first.")

    try:
        # Uruchomienie logiki konwersji
        # Uwaga: pdf2docx jest procesem synchronicznym. 
        # Przy dużym ruchu warto użyć background_tasks lub run_in_threadpool.
        convert_pdf_to_word(input_path, output_path)
        
        return {
            "status": "completed", 
            "original": filename, 
            "converted": output_filename,
            # Link pasuje do Twojego wolumenu w Nginx
            "download_url": f"/downloads/{output_filename}" 
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))