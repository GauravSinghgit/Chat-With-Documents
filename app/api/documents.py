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
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_llm_service,
    get_vectorstore_service,
)
from app.models import Document, User
from app.schemas import DocumentListResponse, DocumentResponse
from app.services.llm import LLMService
from app.services.vectorstore import VectorStoreService
from app.utils.logger import logger
from app.utils.rate_limit import limiter
from app.utils.security import sanitize_input

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {".txt", ".pdf", ".md"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ─── Upload (single or multiple) ─────────────────────────────────────────────


@router.post("/ingest", status_code=201)
@limiter.limit("10/minute")
async def ingest_documents(
    request: Request,
    files: list[UploadFile] = File(...),
    generate_summary: bool = Query(default=True),
    db: Session = Depends(get_db),
    vectorstore: VectorStoreService = Depends(get_vectorstore_service),
    llm_service: LLMService = Depends(get_llm_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict[str, Any]:
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per request")

    results: list[dict[str, Any]] = []
    for file in files:
        try:
            result = await _process_single_file(
                file, db, vectorstore, llm_service, current_user, generate_summary
            )
            results.append(result)
        except HTTPException as e:
            results.append({"filename": file.filename, "error": e.detail})
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            results.append(
                {
                    "filename": file.filename,
                    "error": "Failed to process file. Please check the file and try again.",
                }
            )

    return {"ingested": len([r for r in results if "error" not in r]), "results": results}


async def _process_single_file(
    file: UploadFile,
    db: Session,
    vectorstore: VectorStoreService,
    llm_service: LLMService,
    current_user: User | None,
    generate_summary: bool,
) -> dict[str, Any]:
    filename = file.filename or "unnamed"
    ext = os.path.splitext(filename)[-1].lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_TYPES)}",
        )

    content_bytes = await file.read()
    if len(content_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max size: 10 MB")

    # Extract text
    raw_text, page_count = _extract_text(content_bytes, ext, filename)
    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from file")

    sanitized = sanitize_input(raw_text)

    # Generate summary (first 2000 chars to keep token count low)
    summary = None
    if generate_summary:
        try:
            summary_prompt = f"Summarize this document in 2-3 sentences:\n\n{sanitized[:2000]}"
            summary = await llm_service.generate(summary_prompt)
            summary = summary[:500]
        except Exception as e:
            logger.warning(f"Summary generation failed for {filename}: {e}")

    # Save to DB
    doc = Document(
        user_id=current_user.id if current_user else None,
        filename=filename,
        original_filename=filename,
        file_type=ext.lstrip("."),
        file_size=len(content_bytes),
        content=sanitized,
        page_count=page_count,
        status="processing",
        summary=summary,
        file_metadata=json.dumps(
            {
                "size_bytes": len(content_bytes),
                "pages": page_count,
                "ext": ext,
            }
        ),
    )
    db.add(doc)
    db.commit()

    # Chunk & embed (PGVector embeds internally via the configured model)
    chunks = _chunk_text(sanitized)
    vectorstore.add_documents(
        chunks,
        [{"doc_id": doc.id, "filename": filename, "page": i} for i in range(len(chunks))],
    )

    doc.chunk_count = len(chunks)
    doc.status = "indexed"
    db.commit()

    logger.info(f"Ingested '{filename}' → {len(chunks)} chunks, {page_count} pages")
    return {
        "document_id": doc.id,
        "filename": filename,
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
    file_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> DocumentListResponse:
    query = db.query(Document)
    if current_user:
        query = query.filter(Document.user_id == current_user.id)
    if file_type:
        query = query.filter(Document.file_type == file_type.lstrip("."))

    total = query.count()
    docs = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return DocumentListResponse(
        total=total, documents=[DocumentResponse.model_validate(d) for d in docs]
    )


# ─── Get Single Document ──────────────────────────────────────────────────────


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> Document:
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
) -> None:
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
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
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
    vectorstore.add_documents(
        chunks,
        [{"doc_id": doc.id, "filename": doc.filename} for _ in chunks],
    )

    doc.chunk_count = len(chunks)
    doc.status = "indexed"
    db.commit()
    logger.info(f"Re-indexed document {document_id}")
    return {"document_id": document_id, "chunks": len(chunks), "status": "indexed"}


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _extract_text(content_bytes: bytes, ext: str, filename: str) -> tuple[str, int]:
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
            text = "\n\n".join(f"[Page {i + 1}]\n{page.get_text()}" for i, page in enumerate(doc))
            doc.close()
            return text, pages
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"PDF extraction failed: {e}") from e
        finally:
            # Always clean up tmp file regardless of success/error
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    raise HTTPException(status_code=400, detail=f"Unsupported extension: {ext}")


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 60) -> list[str]:
    """Split text into overlapping word-level chunks."""
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks
