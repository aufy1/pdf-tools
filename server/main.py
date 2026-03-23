import os
import shutil
import fitz
import time
import zipfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.requests import MergeRequest, SplitRequest

from logic import process_pdf_translation
from converters import convert_pdf_to_word
from typing import List

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

# -------------------------------------------------------------
# FUNKCJE POMOCNICZE
# -------------------------------------------------------------
def parse_page_ranges(pages_str: str, max_pages: int) -> List[int]:
    """Konwertuje string np. '1-3, 5' na listę indeksów stron (od 0)."""
    pages_to_extract = set()
    parts = [p.strip() for p in pages_str.split(',')]
    for part in parts:
        if '-' in part:
            start, end = part.split('-')
            start_idx = max(0, int(start) - 1)
            end_idx = min(max_pages - 1, int(end) - 1)
            pages_to_extract.update(range(start_idx, end_idx + 1))
        else:
            idx = int(part) - 1
            if 0 <= idx < max_pages:
                pages_to_extract.add(idx)
    return sorted(list(pages_to_extract))

# -------------------------------------------------------------
# ENDPOINTY
# -------------------------------------------------------------
@app.get("/")
def read_root():
    return {"status": "Backend is running", "service": "BabelDOC AI Translator"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "status": "uploaded"}

@app.post("/merge")
async def merge_pdfs(request: MergeRequest):
    if len(request.filenames) < 2:
        raise HTTPException(status_code=400, detail="Wymagane są minimum 2 pliki do połączenia.")

    merged_pdf = fitz.open()  # Pusty dokument
    
    try:
        for fname in request.filenames:
            file_path = os.path.join(UPLOAD_DIR, fname)
            if not os.path.exists(file_path):
                merged_pdf.close()
                raise HTTPException(status_code=404, detail=f"Plik {fname} nie został znaleziony.")
            
            doc_to_insert = fitz.open(file_path)
            merged_pdf.insert_pdf(doc_to_insert)
            doc_to_insert.close()
            
        timestamp = int(time.time())
        output_filename = f"merged_{timestamp}.pdf"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        merged_pdf.save(output_path)
        merged_pdf.close()
        
        return {
            "status": "completed", 
            "converted": output_filename,
            "download_url": f"/downloads/{output_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/split")
async def split_pdf(request: SplitRequest):
    input_path = os.path.join(UPLOAD_DIR, request.filename)
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="Plik nie został znaleziony.")

    try:
        doc = fitz.open(input_path)
        total_pages = doc.page_count
        base_name = os.path.splitext(request.filename)[0]
        timestamp = int(time.time())

        if request.pages:
            try:
                pages_to_extract = parse_page_ranges(request.pages, total_pages)
            except ValueError:
                doc.close()
                raise HTTPException(status_code=400, detail="Nieprawidłowy format zakresu stron.")
                
            if not pages_to_extract:
                doc.close()
                raise HTTPException(status_code=400, detail="Brak stron pasujących do podanego zakresu.")

            doc.select(pages_to_extract)
                
            output_filename = f"split_{base_name}_{timestamp}.pdf"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            doc.save(output_path)
            doc.close()
                
            return {
                "status": "completed", 
                "converted": output_filename,
                "download_url": f"/downloads/{output_filename}"
            }

        else:
            zip_filename = f"split_{base_name}_{timestamp}.zip"
            zip_path = os.path.join(OUTPUT_DIR, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i in range(total_pages):
                    single_page_doc = fitz.open()
                    single_page_doc.insert_pdf(doc, from_page=i, to_page=i)
                    
                    page_filename = f"{base_name}_strona_{i+1}.pdf"
                    page_path = os.path.join(OUTPUT_DIR, page_filename)
                    
                    single_page_doc.save(page_path)
                    single_page_doc.close()
                        
                    zipf.write(page_path, page_filename)
                    os.remove(page_path)
                    
            doc.close()
            return {
                "status": "completed", 
                "converted": zip_filename,
                "download_url": f"/downloads/{zip_filename}"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate/{filename}")
async def translate_document(filename: str, target_lang: str = "uk"):
    input_path = os.path.join(UPLOAD_DIR, filename)
    output_filename = f"{target_lang.upper()}_{filename}"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        process_pdf_translation(
            input_path, 
            output_path, 
            source_lang='pl', 
            target_lang=target_lang.lower()
        )
        
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