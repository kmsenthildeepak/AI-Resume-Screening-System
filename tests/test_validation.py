"""
Tests for validation and export functions in exporter.py
Covers:
- Formula injection sanitization (=, +, -, @, \t)
- CSV generation with standard and Unicode characters
- CSV column integrity and structure
- Exporting partial extraction failures safely
"""

import csv
import io
import pytest
from exporter import sanitize_csv_cell, generate_candidates_csv


def test_sanitize_csv_cell_formula_injection():
    # Test spreadsheet formula characters
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("+cmd|'/c calc'!A0") == "'+cmd|'/c calc'!A0"
    assert sanitize_csv_cell("-5+2") == "'-5+2"
    assert sanitize_csv_cell("@SUM(1,2)") == "'@SUM(1,2)"
    assert sanitize_csv_cell("\tTAB") == "'\tTAB"


def test_sanitize_csv_cell_normal_values():
    assert sanitize_csv_cell("Normal Text") == "Normal Text"
    assert sanitize_csv_cell("Python, Docker") == "Python, Docker"
    assert sanitize_csv_cell(95.5) == "95.5"
    assert sanitize_csv_cell(None) == ""


def test_generate_candidates_csv_structure():
    candidates = [
        {
            "rank": 1,
            "candidate_id": "CAND_001_alex.txt",
            "filename": "alex.txt",
            "name": "Alex Morgan",
            "emails": ["alex@example.com"],
            "phones": ["555-1234"],
            "overall_score": 85.5,
            "text_similarity_score": 80.0,
            "skill_match_score": 90.0,
            "matched_skills": ["Java", "Docker"],
            "missing_skills": ["Kafka"],
            "education_evidence": ["B.S. in Computer Science"],
            "experience_evidence": ["5+ years experience"],
            "success": True,
            "error": None
        },
        {
            "rank": 2,
            "candidate_id": "CAND_002_corrupted.pdf",
            "filename": "corrupted.pdf",
            "name": None,
            "emails": [],
            "phones": [],
            "overall_score": 0.0,
            "text_similarity_score": 0.0,
            "skill_match_score": 0.0,
            "matched_skills": [],
            "missing_skills": ["Java", "Docker", "Kafka"],
            "education_evidence": [],
            "experience_evidence": [],
            "success": False,
            "error": "File corrupted"
        }
    ]

    csv_text = generate_candidates_csv(candidates)
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    # 1 header row + 2 data rows
    assert len(rows) == 3

    header = rows[0]
    assert "Rank" in header
    assert "Candidate ID" in header
    assert "Overall Score (%)" in header
    assert "Matched Skills" in header

    # Candidate 1 checks
    assert rows[1][0] == "1"
    assert rows[1][2] == "alex.txt"
    assert rows[1][3] == "Alex Morgan"
    assert "Success" in rows[1][13]

    # Candidate 2 failure checks
    assert rows[2][0] == "2"
    assert rows[2][2] == "corrupted.pdf"
    assert "Failed" in rows[2][13]
    assert "File corrupted" in rows[2][14]


def test_generate_candidates_csv_unicode():
    candidates = [
        {
            "rank": 1,
            "candidate_id": "CAND_001_rené.txt",
            "filename": "rené_müller.txt",
            "name": "René Müller",
            "emails": ["rene@example.fr"],
            "phones": [],
            "overall_score": 75.0,
            "text_similarity_score": 70.0,
            "skill_match_score": 80.0,
            "matched_skills": ["Python"],
            "missing_skills": [],
            "education_evidence": [],
            "experience_evidence": [],
            "success": True,
            "error": None
        }
    ]
    csv_text = generate_candidates_csv(candidates)
    assert "René Müller" in csv_text
    assert "rené_müller.txt" in csv_text
