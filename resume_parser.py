"""
Resume Parser Module for extracting text and candidate information from resumes.
Supports PDF, DOCX, and TXT files.
"""

import io
import re
from typing import Dict, Any, List, Optional
import pypdf
import docx

from config import MAX_FILE_SIZE_BYTES, SUPPORTED_EXTENSIONS, EDUCATION_KEYWORDS, EXPERIENCE_KEYWORDS


# Regex patterns for contact information
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b"
)

# Potential degree detection pattern
DEGREE_PATTERN = re.compile(
    r"\b(B\.?Tech|BTech|B\.?E|BE|B\.?S|BS|B\.?Sc|BSc|BCA|Bachelor(?:'s)?|"
    r"M\.?Tech|MTech|M\.?E|ME|M\.?S|MS|M\.?Sc|MSc|MCA|Master(?:'s)?|"
    r"Ph\.?D|PhD|Doctorate)\b",
    re.IGNORECASE
)

# Year of experience pattern (e.g. "5+ years", "3 years of experience", "2-3 years")
EXP_YEARS_PATTERN = re.compile(
    r"\b(\d{1,2}(?:\+|-|\s*to\s*\d{1,2})?\s*(?:years?|yrs?)(?:\s+of)?\s+experience)\b",
    re.IGNORECASE
)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using pypdf."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise ValueError("PDF is password-protected and cannot be read.")

        text_parts = []
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        full_text = "\n".join(text_parts).strip()
        if not full_text:
            raise ValueError(
                "No readable text could be extracted from PDF. "
                "The file may be scanned, image-only, or contain non-extractable content (OCR is not supported)."
            )
        return full_text
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error parsing PDF file: {str(e)}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX paragraphs and tables using python-docx."""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text_parts = []

        # Extract paragraphs
        for p in doc.paragraphs:
            p_text = p.text.strip()
            if p_text:
                text_parts.append(p_text)

        # Extract text inside tables
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    text_parts.append(row_text)

        full_text = "\n".join(text_parts).strip()
        if not full_text:
            raise ValueError("DOCX document contains no readable text or is empty.")
        return full_text
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error parsing DOCX file: {str(e)}")


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from plain text file trying multiple encodings."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            text = file_bytes.decode(enc).strip()
            if not text:
                raise ValueError("TXT file is empty.")
            return text
        except UnicodeDecodeError:
            continue
        except ValueError:
            raise

    raise ValueError("Unable to decode text file with standard encodings (UTF-8, Latin-1, CP1252).")


def extract_raw_text(file_bytes: bytes, filename: str) -> str:
    """Dispatch file extraction based on file extension."""
    if not file_bytes:
        raise ValueError("File is empty (0 bytes).")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB.")

    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lower_name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    elif lower_name.endswith(".txt"):
        return extract_text_from_txt(file_bytes)
    else:
        ext = lower_name.split(".")[-1] if "." in lower_name else "unknown"
        raise ValueError(f"Unsupported file format (.{ext}). Supported formats: PDF, DOCX, TXT.")


def extract_candidate_name(text: str) -> Optional[str]:
    """
    Heuristic name extraction:
    Assumes candidate name appears in the first few non-empty lines,
    before common headers like 'Objective', 'Summary', 'Experience', 'Education', 'Email', etc.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return None

    # Check top 5 lines for candidate name
    for line in lines[:5]:
        # Skip if contains email, phone, url, or typical section titles
        if EMAIL_REGEX.search(line) or PHONE_REGEX.search(line) or "http" in line.lower() or "github" in line.lower():
            continue
        if any(h in line.lower() for h in ["resume", "curriculum vitae", "cv", "summary", "profile", "objective", "contact"]):
            continue
        
        # Name is usually 2 to 4 words, letters only, reasonable length
        words = line.split()
        if 2 <= len(words) <= 4:
            cleaned = re.sub(r"[^\w\s\.-]", "", line)
            # check if mostly alphabetic
            if all(w.replace(".", "").replace("-", "").isalpha() for w in words):
                return cleaned

    # Fallback to first valid line if short
    first_line = lines[0]
    words = first_line.split()
    if 1 <= len(words) <= 4 and len(first_line) < 40 and not any(c in first_line for c in ["@", ":", "/", "\\"]):
        return first_line

    return None


def extract_emails(text: str) -> List[str]:
    """Extract unique valid email addresses from text."""
    matches = EMAIL_REGEX.findall(text)
    # Deduplicate while preserving order
    seen = set()
    emails = []
    for m in matches:
        m_clean = m.strip(".,;:()")
        if m_clean.lower() not in seen:
            seen.add(m_clean.lower())
            emails.append(m_clean)
    return emails


def extract_phones(text: str) -> List[str]:
    """Extract phone numbers from text."""
    matches = PHONE_REGEX.findall(text)
    seen = set()
    phones = []
    for m in matches:
        m_clean = m.strip(".,;: \t\r\n")
        # Filter out numbers that are just 4 digits (like years) or too short
        digits = re.sub(r"\D", "", m_clean)
        if 10 <= len(digits) <= 15 and digits not in seen:
            seen.add(digits)
            phones.append(m_clean)
    return phones


def extract_education_evidence(text: str) -> List[str]:
    """
    Extract snippets/lines containing education information for recruiter verification.
    """
    evidence = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    for line in lines:
        if DEGREE_PATTERN.search(line) or any(k in line.lower() for k in ["bachelor", "master", "doctorate", "degree in", "b.tech", "m.tech", "ph.d"]):
            # Add line as evidence
            clean_line = line.strip(" -*•\t")
            if clean_line and clean_line not in evidence and len(clean_line) < 200:
                evidence.append(clean_line)

    return evidence[:5]  # Limit to top 5 evidence snippets


def extract_experience_evidence(text: str) -> List[str]:
    """
    Extract snippets/lines containing experience indicators.
    """
    evidence = []
    # 1. Search for years of experience pattern
    for match in EXP_YEARS_PATTERN.finditer(text):
        snippet = match.group(0).strip()
        if snippet and snippet not in evidence:
            evidence.append(snippet)

    # 2. Search for lines containing job titles / experience context
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines:
        line_lower = line.lower()
        if any(w in line_lower for w in ["software engineer", "developer", "data scientist", "system analyst", "lead architect", "internship"]):
            clean_line = line.strip(" -*•\t")
            if clean_line and clean_line not in evidence and len(clean_line) < 200:
                evidence.append(clean_line)

    return evidence[:5]  # Limit to top 5 snippets


def parse_resume(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Full parse pipeline for a resume document.
    Returns structured dictionary with extracted information or error message.
    """
    result: Dict[str, Any] = {
        "filename": filename,
        "success": False,
        "error": None,
        "warning": None,
        "raw_text": "",
        "name": None,
        "emails": [],
        "phones": [],
        "education_evidence": [],
        "experience_evidence": []
    }

    try:
        raw_text = extract_raw_text(file_bytes, filename)
        result["raw_text"] = raw_text
        result["name"] = extract_candidate_name(raw_text)
        result["emails"] = extract_emails(raw_text)
        result["phones"] = extract_phones(raw_text)
        result["education_evidence"] = extract_education_evidence(raw_text)
        result["experience_evidence"] = extract_experience_evidence(raw_text)
        result["success"] = True

        # Check for very sparse text (e.g. scanned/partial PDF or placeholder document)
        word_count = len(raw_text.split())
        if word_count < 25:
            result["warning"] = (
                f"Document contains very limited extractable text ({word_count} words). "
                "The file may be a minimal placeholder, partially flattened, or contain image elements that require OCR."
            )
    except Exception as e:
        result["error"] = str(e)
        result["success"] = False

    return result
