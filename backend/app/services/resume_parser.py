"""
Extract plain text from PDF and DOCX resume files.
"""

from io import BytesIO

from docx import Document
from pypdf import PdfReader


class ResumeParseError(Exception):
    """Raised when a file cannot be parsed or is empty."""

    pass


def extract_text_from_pdf(data: bytes) -> str:
    """Read all pages from a PDF and concatenate text."""
    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts).strip()


def extract_text_from_docx(data: bytes) -> str:
    """Extract paragraphs from a Word document."""
    doc = Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()


def extract_resume_text(filename: str, data: bytes) -> str:
    """
    Dispatch to the correct parser based on file extension.
    Raises ResumeParseError if format is unsupported or text is empty.
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        text = extract_text_from_pdf(data)
    elif lower.endswith(".docx"):
        text = extract_text_from_docx(data)
    else:
        raise ResumeParseError("Unsupported file type. Use PDF or DOCX.")

    if not text:
        raise ResumeParseError(
            "Could not extract text from the file. Try another export or format."
        )

    return text
