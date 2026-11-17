import io
from typing import Tuple, Optional
from pypdf import PdfReader


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts embedded textual content from digital PDF medical reports using pypdf.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        return "\n".join(pages_text).strip()
    except Exception as e:
        print(f"[ReportParser] PDF text extraction warning: {e}")
        return ""


def inspect_report_file(file_bytes: bytes, filename: str) -> Tuple[str, Optional[str]]:
    """
    Determines whether the uploaded report has extractable vector text or requires multimodal vision.
    Returns: (extracted_text, mime_type)
    """
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
        return text, "application/pdf"
    elif lower_name.endswith(".txt"):
        try:
            return file_bytes.decode("utf-8", errors="ignore"), "text/plain"
        except Exception:
            return "", "text/plain"
    elif lower_name.endswith(".png"):
        return "", "image/png"
    elif lower_name.endswith(".jpg") or lower_name.endswith(".jpeg"):
        return "", "image/jpeg"
    elif lower_name.endswith(".webp"):
        return "", "image/webp"
    return "", None
