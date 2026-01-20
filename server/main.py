# /server/main.py
import os
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from logic import process_pdf_translation

app = FastAPI()

# Konfiguracja CORS (żeby React mógł gadać z Pythonem)
origins = [
    "http://localhost:5173",
    "http://localhost:8098",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
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
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Uruchamiamy proces tłumaczenia (synchronicznie dla uproszczenia w MVP, 
    # docelowo w Celery/BackgroundTasks)
    try:
        process_pdf_translation(input_path, output_path)
        return {
            "status": "completed", 
            "original": filename, 
            "translated": output_filename,
            "download_url": f"http://localhost:8000/download/{output_filename}"
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")