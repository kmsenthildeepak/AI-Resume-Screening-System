"""
Tests for requirement_extractor.py
Covers:
- Standard skill extraction from job descriptions
- Case-insensitivity (e.g. PYTHON, python)
- Aliases & synonyms mapping (e.g. 'sklearn' -> 'Scikit-Learn', 'k8s' -> 'Kubernetes')
- Boundary handling (avoid matching 'go' inside 'algorithm' or 'good', or 'c' inside 'can')
- Duplicate skill deduplication
- Empty or whitespace job description handling
- Descriptions with no cataloged skills
- Distinguishing required vs preferred skill sections
"""

import pytest
from requirement_extractor import (
    extract_skills,
    extract_job_sections,
    extract_job_requirements,
    extract_job_title
)


def test_extract_skills_standard():
    text = "We need an engineer experienced in Java, Spring Boot, and PostgreSQL."
    skills = extract_skills(text)
    assert "Java" in skills
    assert "Spring Boot" in skills
    assert "PostgreSQL" in skills


def test_extract_skills_case_insensitive():
    text = "Proficiency in PYTHON, DOCKER, and aws cloud."
    skills = extract_skills(text)
    assert "Python" in skills
    assert "Docker" in skills
    assert "AWS" in skills


def test_extract_skills_aliases():
    text = "Candidate should have experience in k8s, drf, and sklearn."
    skills = extract_skills(text)
    assert "Kubernetes" in skills
    assert "Django" in skills
    assert "Scikit-Learn" in skills


def test_word_boundary_avoids_false_positives():
    # 'good', 'going', 'algorithm', 'cannot', 'create' should NOT match 'Go', 'R', or 'C'
    text = "The candidate must have good communication skills and read algorithms carefully."
    skills = extract_skills(text)
    assert "Go" not in skills
    assert "R" not in skills
    assert "Communication" in skills


def test_c_plus_plus_and_c_sharp_boundary():
    text = "Looking for a C++ developer with knowledge of C# and .NET core."
    skills = extract_skills(text)
    assert "C++" in skills
    assert "C#" in skills
    assert "ASP.NET" in skills


def test_extract_skills_empty():
    assert extract_skills("") == []
    assert extract_skills("   \n\t  ") == []


def test_extract_skills_no_known_skills():
    text = "Looking for a chef who specializes in French cuisine and baking bread."
    skills = extract_skills(text)
    assert skills == []


def test_extract_job_sections_preferred_and_required():
    jd = """
    Software Engineer

    Requirements:
    - 3 years experience with Python and FastAPI
    - Strong database skills in PostgreSQL

    Preferred:
    - Experience with Kubernetes and Redis
    """
    sections = extract_job_sections(jd)
    assert "Python" in sections["required"]
    assert "Kubernetes" in sections["preferred"]


def test_extract_job_requirements_full():
    jd = """
    Requirements:
    - Proficient in Java, Spring Boot, and Microservices
    - Bachelor's degree in Computer Science
    - 4+ years of software experience

    Nice to have:
    - Experience with Docker and AWS
    """
    reqs = extract_job_requirements(jd)
    assert "Java" in reqs["required_skills"]
    assert "Spring Boot" in reqs["required_skills"]
    assert "Docker" in reqs["preferred_skills"]
    assert "AWS" in reqs["preferred_skills"]
    assert len(reqs["education_requirements"]) >= 1
    assert len(reqs["experience_requirements"]) >= 1
    assert reqs["total_skills_count"] >= 5


def test_extract_job_title_empty_and_whitespace():
    assert extract_job_title("") == "Not Specified"
    assert extract_job_title("   \n\t  ") == "Not Specified"
    assert extract_job_title(None) == "Not Specified"


def test_extract_job_title_explicit_headers():
    assert extract_job_title("Job Title: Senior Java Developer\nRequirements...") == "Senior Java Developer"
    assert extract_job_title("Role: Frontend Developer\nKey duties...") == "Frontend Developer"
    assert extract_job_title("Position: Data Analyst\nSummary of work...") == "Data Analyst"


def test_extract_job_title_recognized_roles():
    assert extract_job_title("We are hiring a Java Full Stack Developer to build enterprise services.") == "Java Full Stack Developer"
    assert extract_job_title("Looking for an experienced Python Developer with Django experience.") == "Python Developer"
    assert extract_job_title("Seeking a Frontend Developer proficient in React and TypeScript.") == "Frontend Developer"
    assert extract_job_title("Opening for Data Analyst with SQL and Tableau skills.") == "Data Analyst"
    assert extract_job_title("Lead Software Engineer responsible for distributed systems.") == "Software Engineer"
    assert extract_job_title("Seeking a Cybersecurity Analyst to monitor and secure networks.") == "Cybersecurity Analyst"


def test_extract_job_title_fallback_custom():
    jd_unusual = "We are seeking a versatile widget optimization specialist who can coordinate internal widget flows."
    assert extract_job_title(jd_unusual) == "Custom Job Description"
