from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from io import BytesIO
import os
from extractor import extract_text_and_metadata, extract_tables, generate_summary

import nltk
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


app = FastAPI()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "text": "",
            "summary": "",
            "metadata": {},
            "tables": [],
            "error": "Only PDF files are allowed."
        })

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        data = extract_text_and_metadata(file_path)
        tables = extract_tables(file_path)
        summary = generate_summary(data["text"])
    except Exception as e:
        os.remove(file_path)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "text": "",
            "summary": "",
            "metadata": {},
            "tables": [],
            "error": f"Error: {str(e)}"
        })

    os.remove(file_path)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "text": data["text"],
        "summary": summary,
        "metadata": data["metadata"],
        "tables": tables,
        "error": ""
    })

@app.post("/download-text")
async def download_text(text: str = Form(...)):
    file_stream = BytesIO()
    file_stream.write(text.encode("utf-8"))
    file_stream.seek(0)
    return StreamingResponse(file_stream, media_type="text/plain", headers={
        "Content-Disposition": "attachment; filename=extracted_text.txt"
    })
