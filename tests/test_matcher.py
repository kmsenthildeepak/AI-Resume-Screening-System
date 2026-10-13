"""
Tests for matcher.py
Covers:
- TF-IDF and Cosine similarity computation
- Pure NumPy cosine similarity boundary safety (zero norm, identical vectors)
- Synthetic matching accuracy: relevant resume outranks unrelated resume
- Finite score constraints (all values between 0.0 and 100.0)
- Candidate ordering is strictly descending by score
- Matched and missing skills accuracy
- Deterministic results across multiple runs
- Handling duplicate filenames safely
"""

import numpy as np
import pytest
from matcher import (
    compute_cosine_similarity,
    compute_tfidf_similarities,
    calculate_skill_match_score,
    rank_resumes
)


def test_cosine_similarity_identical_and_zero():
    v1 = np.array([1.0, 2.0, 3.0])
    v2 = np.array([1.0, 2.0, 3.0])
    zero = np.array([0.0, 0.0, 0.0])

    sim_identical = compute_cosine_similarity(v1, v2)
    assert pytest.approx(sim_identical, 0.001) == 1.0

    sim_zero = compute_cosine_similarity(v1, zero)
    assert sim_zero == 0.0


def test_compute_tfidf_similarities():
    query = "Python machine learning engineer with Scikit-Learn"
    docs = [
        "Experienced Python machine learning developer with Scikit-Learn expertise",
        "Cook and baker specializing in pastries and cakes"
    ]
    sims = compute_tfidf_similarities(query, docs)
    assert len(sims) == 2
    assert sims[0] > sims[1]
    assert sims[0] > 0.4
    assert sims[1] == 0.0


def test_calculate_skill_match_score_with_preferred():
    cand_skills = ["Java", "Spring Boot", "Docker"]
    job_req = ["Java", "Spring Boot", "PostgreSQL"]
    job_pref = ["Docker", "AWS"]

    res = calculate_skill_match_score(cand_skills, job_req, job_pref)
    assert "Java" in res["matched_skills"]
    assert "Spring Boot" in res["matched_skills"]
    assert "Docker" in res["matched_skills"]
    assert "PostgreSQL" in res["missing_skills"]
    assert "AWS" in res["missing_skills"]
    assert 0.0 <= res["score"] <= 1.0


def test_strong_match_outranks_unrelated_resume():
    jd = "Seeking a Java Backend Engineer with Spring Boot, PostgreSQL, and Docker."
    r_strong = {
        "filename": "strong.txt",
        "success": True,
        "raw_text": "Java backend developer with 4 years experience in Spring Boot, PostgreSQL, and Docker."
    }
    r_unrelated = {
        "filename": "unrelated.txt",
        "success": True,
        "raw_text": "Executive chef preparing fine dining Italian dishes and pasta."
    }

    ranked = rank_resumes(jd, [r_unrelated, r_strong])
    assert len(ranked) == 2
    assert ranked[0]["filename"] == "strong.txt"
    assert ranked[1]["filename"] == "unrelated.txt"
    assert ranked[0]["overall_score"] > ranked[1]["overall_score"]
    assert ranked[0]["rank"] == 1
    assert ranked[1]["rank"] == 2


def test_scores_strictly_bounded_between_0_and_100():
    jd = "Data scientist specializing in Python, Machine Learning, and SQL."
    resumes = [
        {"filename": "r1.txt", "success": True, "raw_text": "Python ML SQL expert."},
        {"filename": "r2.txt", "success": True, "raw_text": "Some text."},
        {"filename": "r3.txt", "success": False, "error": "Failed"}
    ]
    ranked = rank_resumes(jd, resumes)
    for c in ranked:
        assert 0.0 <= c["overall_score"] <= 100.0
        assert 0.0 <= c["text_similarity_score"] <= 100.0
        assert 0.0 <= c["skill_match_score"] <= 100.0


def test_duplicate_filenames_distinguishable():
    jd = "Python engineer"
    r1 = {"filename": "resume.pdf", "success": True, "raw_text": "Python engineer"}
    r2 = {"filename": "resume.pdf", "success": True, "raw_text": "Python junior"}

    ranked = rank_resumes(jd, [r1, r2])
    assert len(ranked) == 2
    # Ensure distinct candidate IDs
    assert ranked[0]["candidate_id"] != ranked[1]["candidate_id"]


def test_deterministic_ranking():
    jd = "React frontend developer with TypeScript and CSS"
    resumes = [
        {"filename": "c1.txt", "success": True, "raw_text": "React TypeScript developer"},
        {"filename": "c2.txt", "success": True, "raw_text": "Frontend CSS developer"},
    ]
    run1 = rank_resumes(jd, resumes)
    run2 = rank_resumes(jd, resumes)
    assert [r["overall_score"] for r in run1] == [r["overall_score"] for r in run2]
    assert [r["filename"] for r in run1] == [r["filename"] for r in run2]
