"""
Tests for resume_parser.py
Covers:
- TXT file extraction (valid, Unicode, empty)
- DOCX extraction (valid, table text, empty, corrupted)
- PDF extraction (valid text-based, corrupted, empty)
- Unsupported extensions
- File size boundary checks
- Name, Email, and Phone extraction heuristics
"""

import io
import pytest
import docx
from resume_parser import (
    extract_text_from_txt,
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_raw_text,
    extract_candidate_name,
    extract_emails,
    extract_phones,
    extract_education_evidence,
    extract_experience_evidence,
    parse_resume
)


def test_txt_valid_extraction():
    content = "John Doe\nSoftware Engineer\nPython developer with 5 years experience."
    raw = extract_text_from_txt(content.encode("utf-8"))
    assert "John Doe" in raw
    assert "Python developer" in raw


def test_txt_unicode_extraction():
    content = "René Müller\nIngénieur Logiciel\nCompétences: Python, Docker, C++."
    raw = extract_text_from_txt(content.encode("utf-8"))
    assert "René Müller" in raw
    assert "Ingénieur" in raw


def test_txt_empty_raises_value_error():
    with pytest.raises(ValueError, match="TXT file is empty"):
        extract_text_from_txt(b"")


def test_docx_valid_extraction():
    doc = docx.Document()
    doc.add_paragraph("Alice Johnson")
    doc.add_paragraph("Machine Learning Engineer")
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Skills"
    table.cell(0, 1).text = "Python, PyTorch"
    
    bio = io.BytesIO()
    doc.save(bio)
    raw = extract_text_from_docx(bio.getvalue())

    assert "Alice Johnson" in raw
    assert "Machine Learning Engineer" in raw
    assert "PyTorch" in raw


def test_docx_empty_raises_value_error():
    doc = docx.Document()
    bio = io.BytesIO()
    doc.save(bio)
    with pytest.raises(ValueError, match="DOCX document contains no readable text"):
        extract_text_from_docx(bio.getvalue())


def test_docx_malformed_raises_value_error():
    with pytest.raises(ValueError, match="Error parsing DOCX file"):
        extract_text_from_docx(b"corrupted not a zip docx")


def test_pdf_valid_extraction():
    # Valid minimal PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj
4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
5 0 obj << /Length 60 >> stream
BT
/F1 12 Tf
72 712 Td
(David Kim - Python Developer david@example.com) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000227 00000 n 
0000000298 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
409
%%EOF"""
    raw = extract_text_from_pdf(pdf_content)
    assert "David Kim" in raw
    assert "Python Developer" in raw


def test_pdf_malformed_raises_value_error():
    with pytest.raises(ValueError, match="Error parsing PDF file"):
        extract_text_from_pdf(b"not a valid pdf header")


def test_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_raw_text(b"some data", "resume.png")


def test_file_size_exceeded():
    large_bytes = b"A" * (11 * 1024 * 1024)  # 11 MB > 10 MB limit
    with pytest.raises(ValueError, match="File size exceeds maximum allowed limit"):
        extract_raw_text(large_bytes, "resume.txt")


def test_email_extraction():
    sample = "Contact me at candidate.work@domain.com or backup_test123@sub.domain.org."
    emails = extract_emails(sample)
    assert "candidate.work@domain.com" in emails
    assert "backup_test123@sub.domain.org" in emails


def test_phone_extraction():
    sample = "Call me on +1 (555) 234-5678 or 9876543210 for an interview."
    phones = extract_phones(sample)
    assert len(phones) >= 1
    # Check that short numbers or year 2024 are not treated as phones
    assert "2024" not in phones


def test_candidate_name_heuristic():
    sample = "Robert Downey\nSenior Systems Architect\nEmail: robert@example.com\nExperience..."
    name = extract_candidate_name(sample)
    assert name == "Robert Downey"


def test_parse_resume_end_to_end_success():
    txt_bytes = b"Sarah Connor\nEmail: sarah@example.com\nPhone: 555-123-4567\nB.Tech in Computer Science\n5+ years of experience in Java"
    res = parse_resume(txt_bytes, "sarah.txt")
    assert res["success"] is True
    assert res["name"] == "Sarah Connor"
    assert "sarah@example.com" in res["emails"]
    assert len(res["phones"]) == 1
    assert len(res["education_evidence"]) >= 1
    assert len(res["experience_evidence"]) >= 1


def test_parse_resume_end_to_end_failure():
    res = parse_resume(b"", "empty.pdf")
    assert res["success"] is False
    assert "empty" in res["error"].lower()


def test_parse_sample_pdf_resume_04():
    import os
    pdf_path = os.path.join("sample_resumes", "resume_04_python_dev.pdf")
    assert os.path.exists(pdf_path), "resume_04_python_dev.pdf must exist"

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    res = parse_resume(pdf_bytes, "resume_04_python_dev.pdf")
    assert res["success"] is True
    assert res["name"] == "David Kim"
    assert "david.kim@example.com" in res["emails"]
    assert res["warning"] is None, f"Expected no warning, got: {res.get('warning')}"
    # Verify word count exceeds 200 words
    words = res["raw_text"].split()
    assert len(words) >= 200, f"Expected >= 200 words, got {len(words)}"
    # Verify extracted skills
    from requirement_extractor import extract_skills
    skills = extract_skills(res["raw_text"])
    assert "Python" in skills
    assert "Django" in skills
    assert "PostgreSQL" in skills
    assert "Docker" in skills
    assert "Java" in skills
    assert "Spring Boot" in skills
    assert "MySQL" in skills
    assert "REST API" in skills
    assert "Git" in skills
    assert any("berkeley" in str(e).lower() or "computer science" in str(e).lower() for e in res["education_evidence"])
    assert any("engineer" in str(e).lower() for e in res["experience_evidence"])
    assert len(res["phones"]) >= 1
