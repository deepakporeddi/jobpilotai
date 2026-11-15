from pathlib import Path
import fitz
from docx import Document

def extract_resume_text(file_path: str, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        with fitz.open(file_path) as document:
            text = "\n".join(page.get_text("text") for page in document)
        if not text.strip():
            raise ValueError("This PDF has no selectable text. Scanned PDF OCR will be supported in a later milestone; please upload a text-based PDF or DOCX for now.")
        return text.strip()
    if extension == ".docx":
        document = Document(file_path)
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        for table in document.tables:
            for row in table.rows:
                paragraphs.append(" | ".join(cell.text.strip() for cell in row.cells))
        text = "\n".join(paragraphs).strip()
        if not text:
            raise ValueError("No readable text was found in this DOCX file.")
        return text
    raise ValueError("Unsupported file type. Upload a PDF or DOCX file.")

def build_review_profile(text: str) -> dict:
    """Conservative, format-agnostic extraction. Unknown fields remain empty for user review."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    email = next((token.strip(".,;()<>") for line in lines for token in line.split() if "@" in token and "." in token.split("@")[-1]), "")
    import re
    phone_match = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text)
    sections = {}
    current = "summary"
    headings = {
        "experience": ("experience", "employment", "work history", "professional experience"),
        "education": ("education", "academic", "qualification"),
        "skills": ("skills", "technical skills", "core competencies", "technologies"),
        "projects": ("projects", "personal projects", "key projects"),
        "certifications": ("certifications", "certificates", "licenses"),
        "summary": ("summary", "profile", "objective", "about me"),
    }
    for line in lines:
        normalized = line.lower().strip(" :")
        matched = next((key for key, aliases in headings.items() if normalized in aliases), None)
        if matched:
            current = matched
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    name = ""
    for line in lines[:5]:
        if "@" not in line and not re.search(r"\d{3,}", line) and len(line.split()) <= 5 and len(line) < 60:
            name = line
            break
    return {
        "personal_info": {"name": name, "email": email, "phone": phone_match.group(0).strip() if phone_match else ""},
        "summary": "\n".join(sections.get("summary", [])),
        "experience": sections.get("experience", []),
        "education": sections.get("education", []),
        "skills": sections.get("skills", []),
        "projects": sections.get("projects", []),
        "certifications": sections.get("certifications", []),
        "needs_review": True,
    }
