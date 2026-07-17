"""
PDF Service — extracts raw text from PDF bytes using PyMuPDF (fitz).

PyMuPDF is chosen over pdfplumber/pdfminer for its speed and reliability
with both text-based and complex layout PDFs.
"""

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts all text from a PDF given its raw bytes.

    Args:
        pdf_bytes: Raw bytes of the PDF file.

    Returns:
        A single string of all text extracted from the document,
        with pages separated by double newlines.

    Raises:
        ValueError: If the PDF cannot be opened or parsed.
    """
    try:
        # Open the PDF from memory (no temp file needed)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Failed to open PDF: {e}")

    pages_text = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Extract text preserving layout (whitespace-aware)
        text = page.get_text("text")
        if text.strip():
            pages_text.append(text)

    doc.close()

    # Join pages with separator for readability
    full_text = "\n\n--- Page Break ---\n\n".join(pages_text)
    return full_text
