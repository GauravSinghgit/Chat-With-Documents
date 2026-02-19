"""
Enhanced Document API:
- Multi-file upload
- PDF with page tracking
- Auto-summary generation
- List with filters
- Delete (DB + vector store)
- Re-index support
"""
import json
import os
import tempfile
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import (
    get_embedding_service,
    get_llm_service,
    get_vectorstore_service,
    get_current_user_optional,
    get_current_user,
)
from app.models import Document, User
from app.schemas import DocumentResponse, DocumentListResponse
from app.services.embeddings import EmbeddingService
from app.services.llm import LLMService
from app.services.vectorstore import VectorStoreService
from app.utils.rate_limit import limiter
from app.utils.security import sanitize_input
from app.utils.logger import logger

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {".txt", ".pdf", ".md"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ─── Upload (single or multiple) ─────────────────────────────────────────────

@router.post("/ingest", status_code=201)
@limiter.limit("10/minute")
async def ingest_documents(
    request: Request,
    files: List[UploadFile] = File(...),
    generate_summary: bool = Query(default=True),
    db: Session = Depends(get_db),
    vectorstore: VectorStoreService = Depends(get_vectorstore_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    llm_service: LLMService = Depends(get_llm_service),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per request")

    results = []
    for file in files:
        try:
            result = await _process_single_file(
                file, db, vectorstore, embedding_service,
                llm_service, current_user, generate_summary
            )
            results.append(result)
        except HTTPException as e:
            results.append({"filename": file.filename, "error": e.detail})
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            results.append({"filename": file.filename, "error": str(e)})

    return {"ingested": len([r for r in results if "error" not in r]), "results": results}


async def _process_single_file(
    file: UploadFile,
    db: Session,
    vectorstore: VectorStoreService,
    embedding_service: EmbeddingService,
    llm_service: LLMService,
    current_user: Optional[User],
    generate_summary: bool,
):
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_TYPES)}")

    content_bytes = await file.read()
    if len(content_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max size: 10 MB")

    # Extract text
    raw_text, page_count = _extract_text(content_bytes, ext, file.filename)
    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from file")

    sanitized = sanitize_input(raw_text)

    # Generate summary (first 2000 chars to keep token count low)
    summary = None
    if generate_summary:
        try:
            summary_prompt = (
                f"Summarize this document in 2-3 sentences:\n\n{sanitized[:2000]}"
            )
            summary = await llm_service.generate(summary_prompt)
            summary = summary[:500]
        except Exception as e:
            logger.warning(f"Summary generation failed for {file.filename}: {e}")

    # Save to DB
    doc = Document(
        user_id=current_user.id if current_user else None,
        filename=file.filename,
        original_filename=file.filename,
        file_type=ext.lstrip("."),
        file_size=len(content_bytes),
        content=sanitized,
        page_count=page_count,
        status="processing",
        summary=summary,
        file_metadata=json.dumps({
            "size_bytes": len(content_bytes),
            "pages": page_count,
            "ext": ext,
        }),
    )
    db.add(doc)
    db.commit()

    # Chunk & embed
    chunks = _chunk_text(sanitized)
    embeddings = embedding_service.embed_documents(chunks)
    vectorstore.add_documents(
        chunks,
        embeddings,
        [{"doc_id": doc.id, "filename": file.filename, "page": i} for i in range(len(chunks))],
    )

    doc.chunk_count = len(chunks)
    doc.status = "indexed"
    db.commit()

    logger.info(f"Ingested '{file.filename}' → {len(chunks)} chunks, {page_count} pages")
    return {
        "document_id": doc.id,
        "filename": file.filename,
        "chunks": len(chunks),
        "pages": page_count,
        "status": "indexed",
        "summary": summary,
    }


# ─── List Documents ───────────────────────────────────────────────────────────

@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    file_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    query = db.query(Document)
    if current_user:
        query = query.filter(Document.user_id == current_user.id)
    if file_type:
        query = query.filter(Document.file_type == file_type.lstrip("."))

    total = query.count()
    docs = query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return DocumentListResponse(total=total, documents=docs)


# ─── Get Single Document ──────────────────────────────────────────────────────

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user and doc.user_id and doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return doc


# ─── Delete Document ──────────────────────────────────────────────────────────

@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    vectorstore: VectorStoreService = Depends(get_vectorstore_service),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id and doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Remove chunks from vector store
    try:
        vectorstore.delete_by_doc_id(document_id)
    except Exception as e:
        logger.warning(f"Could not remove vectors for doc {document_id}: {e}")

    db.delete(doc)
    db.commit()
    logger.info(f"Deleted document {document_id} ({doc.filename})")


# ─── Re-index Document ────────────────────────────────────────────────────────

@router.post("/{document_id}/reindex")
async def reindex_document(
    document_id: int,
    db: Session = Depends(get_db),
    vectorstore: VectorStoreService = Depends(get_vectorstore_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id and doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Remove old vectors
    try:
        vectorstore.delete_by_doc_id(document_id)
    except Exception:
        pass

    # Re-chunk and embed
    doc.status = "processing"
    db.commit()

    chunks = _chunk_text(doc.content)
    embeddings = embedding_service.embed_documents(chunks)
    vectorstore.add_documents(
        chunks,
        embeddings,
        [{"doc_id": doc.id, "filename": doc.filename} for _ in chunks],
    )

    doc.chunk_count = len(chunks)
    doc.status = "indexed"
    db.commit()
    logger.info(f"Re-indexed document {document_id}")
    return {"document_id": document_id, "chunks": len(chunks), "status": "indexed"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _extract_text(content_bytes: bytes, ext: str, filename: str):
    """Returns (text, page_count)."""
    if ext == ".txt" or ext == ".md":
        return content_bytes.decode("utf-8", errors="ignore"), 1

    if ext == ".pdf":
        tmp_path = None
        try:
            import fitz
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content_bytes)
                tmp_path = tmp.name
            doc = fitz.open(tmp_path)
            pages = doc.page_count
            text = "\n\n".join(
                f"[Page {i + 1}]\n{page.get_text()}" for i, page in enumerate(doc)
            )
            doc.close()
            return text, pages
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"PDF extraction failed: {e}")
        finally:
            # Always clean up tmp file regardless of success/error
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    raise HTTPException(status_code=400, detail=f"Unsupported extension: {ext}")


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 60) -> List[str]:
    """Split text into overlapping word-level chunks."""
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks
