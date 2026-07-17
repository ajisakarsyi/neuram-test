"""
CV Router — handles PDF upload, text extraction, and LLM summarization.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_service import extract_text_from_pdf
from app.services.llm_service import summarize_cv

router = APIRouter()


@router.post(
    "/upload",
    summary="Upload a CV PDF and get a structured summary",
    response_description="Structured JSON with name, location, and work experience summary",
)
async def upload_cv(file: UploadFile = File(...)):
    """
    Accepts a PDF file (CV/Resume), extracts its text content,
    then sends it to an LLM via OpenRouter to produce a structured summary.

    Returns:
        JSON with `name`, `location`, and `work_experience_summary`.
    """
    # Validate that uploaded file is a PDF
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Please upload a .pdf file.",
        )

    # Read raw bytes from the uploaded file
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Step 1: Extract text from PDF
    extracted_text = extract_text_from_pdf(pdf_bytes)
    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from the PDF. It may be image-based or corrupted.",
        )

    # Step 2: Send extracted text to LLM for structured summarization
    summary = await summarize_cv(extracted_text)

    return {
        "filename": file.filename,
        "character_count": len(extracted_text),
        "summary": summary,
    }
