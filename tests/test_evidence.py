"""
Tests for evidence extraction module (extract_skill_evidence)
Covers:
- Categorization into work_experience, project, achievement, skills_list, mention_only
- Concrete metric detection (percentages, user counts, impact verbs)
- Coverage ratio calculation
- Warnings for bare keyword mentions
"""

import pytest
from requirement_extractor import extract_skill_evidence, extract_skills


def test_evidence_tier_work_experience():
    resume_text = """
    Jane Doe
    jane@example.com

    Professional Experience
    Senior Java Developer at Acme Corp
    - Designed and implemented microservices using Java and Spring Boot.
    - Managed relational data models in PostgreSQL.
    """
    skills = ["Java", "Spring Boot", "PostgreSQL"]
    res = extract_skill_evidence(resume_text, skills)

    assert res["evidence_coverage_ratio"] == 1.0
    for sk in skills:
        assert res["evidence_by_skill"][sk]["tier"] in ("work_experience", "achievement")
        assert res["evidence_by_skill"][sk]["is_demonstrated"] is True


def test_evidence_tier_projects():
    resume_text = """
    John Smith
    john@example.com

    Key Projects
    E-Commerce Web Platform
    - Built a high-performance web API with FastAPI and Python.
    - Cached frequent queries with Redis.
    """
    skills = ["Python", "FastAPI", "Redis"]
    res = extract_skill_evidence(resume_text, skills)

    assert res["evidence_coverage_ratio"] == 1.0
    for sk in skills:
        assert res["evidence_by_skill"][sk]["tier"] in ("project", "achievement")
        assert res["evidence_by_skill"][sk]["is_demonstrated"] is True


def test_evidence_tier_achievement_with_metrics():
    resume_text = """
    Alex Taylor

    Work Experience
    Lead Performance Engineer
    - Optimized PostgreSQL query execution, reducing latency by 45%.
    - Scaled Docker container clusters to support 50,000 requests per second.
    """
    skills = ["PostgreSQL", "Docker"]
    res = extract_skill_evidence(resume_text, skills)

    assert res["evidence_by_skill"]["PostgreSQL"]["tier"] == "achievement"
    assert res["evidence_by_skill"]["Docker"]["tier"] == "achievement"


def test_evidence_bare_skills_list_warning():
    resume_text = """
    Candidate X

    Technical Skills
    Python, Docker, Kubernetes, AWS, Kafka

    Experience
    Store Associate
    - Assisted retail customers and handled cashier operations.
    """
    skills = ["Python", "Docker", "Kubernetes", "AWS", "Kafka"]
    res = extract_skill_evidence(resume_text, skills)

    # Skills were only listed under Technical Skills, not demonstrated in Experience/Projects
    assert res["evidence_coverage_ratio"] == 0.0
    assert res["bare_mentions_count"] == 5
    assert len(res["warnings"]) >= 1
    assert "bare keyword mentions" in res["warnings"][0]


def test_evidence_empty_input():
    res = extract_skill_evidence("", [])
    assert res["evidence_by_skill"] == {}
    assert res["evidence_coverage_ratio"] == 0.0
    assert res["warnings"] == []
