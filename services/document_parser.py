import io
import fitz  # PyMuPDF
import docx


def parse_pdf(data: bytes) -> str:
    doc = fitz.open(stream=data, filetype="pdf")
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages).strip()


def parse_docx(data: bytes) -> str:
    document = docx.Document(io.BytesIO(data))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def parse_txt(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").strip()
