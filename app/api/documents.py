from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.schemas import DocumentIngest
from app.database import get_db
from app.models import Document
from app.dependencies import get_vectorstore_service, get_embedding_service
from app.services.vectorstore import VectorStoreService
from app.services.embeddings import EmbeddingService
from app.utils.security import sanitize_input
import json
import fitz
import tempfile
import fitz
import tempfile


# ✅ ADD THIS FUNCTION
async def extract_text_from_file(file: UploadFile):
    content = await file.read()

    # TXT file
    if file.filename.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")

    # PDF file
    elif file.filename.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        doc = fitz.open(tmp_path)
        text = ""

        for page in doc:
            text += page.get_text()

        return text

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")


router = APIRouter()

@router.post("/documents/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    vectorstore: VectorStoreService = Depends(get_vectorstore_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    text_content = await extract_text_from_file(file)

    sanitized_content = sanitize_input(text_content)

    doc = Document(
        filename=file.filename,
        content=sanitized_content,
        metadata=json.dumps({"size": len(sanitized_content)})
    )

    db.add(doc)
    db.commit()

    chunks = _chunk_text(sanitized_content, chunk_size=500)
    embeddings = embedding_service.embed_documents(chunks)

    vectorstore.add_documents(
        chunks,
        embeddings,
        [{"doc_id": doc.id, "filename": file.filename}] * len(chunks)
    )

    return {"status": "success", "document_id": doc.id, "chunks": len(chunks)}

def _chunk_text(text: str, chunk_size: int = 300, overlap: int = 50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks
