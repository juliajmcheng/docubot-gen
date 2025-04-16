from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from app.pdf_loader import extract_text_from_pdf
from app.qa_chain import get_qa_chain, answer_question
from PyPDF2 import PdfReader

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

qa_data = {}

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    with open("temp.pdf", "wb") as f:
        f.write(contents)

    text = extract_text_from_pdf("temp.pdf")
    docsearch, chain = get_qa_chain(text)
    qa_data["docsearch"] = docsearch
    qa_data["chain"] = chain

    # Add title extraction here
    reader = PdfReader("temp.pdf")
    first_page = reader.pages[0].extract_text()
    title = first_page.split("\n")[0]

    return {"message": "PDF processed successfully.", "title": title}

@app.post("/ask/")
async def ask_question(query: str = Form(...)):
    docsearch = qa_data.get("docsearch")
    chain = qa_data.get("chain")
    if not docsearch or not chain:
        return {"answer": "Please upload a PDF first."}
    answer = answer_question(docsearch, chain, query)
    return {"answer": answer}

@app.get("/metadata/")
async def get_metadata():
    try:
        reader = PdfReader("temp.pdf")
        first_page = reader.pages[0].extract_text()
        title_line = first_page.split("\n")[0]
        return {"title": title_line}
    except:
        return {"title": "Could not extract title"}
