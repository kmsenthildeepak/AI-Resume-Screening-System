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


def test_empty_required_with_preferred_never_awards_free_credit():
    """Verify that an empty required category does NOT award 1.0 (80%) free credit."""
    job_req = []
    job_pref = ["Docker", "AWS"]

    # Candidate with 0 skills must get 0.0, not 0.80
    res_zero = calculate_skill_match_score([], job_req, job_pref)
    assert res_zero["score"] == 0.0
    assert res_zero["required_score"] == 0.0
    assert res_zero["preferred_score"] == 0.0

    # Candidate matching 1 of 2 preferred skills gets 0.50, not 0.90
    res_half = calculate_skill_match_score(["Docker"], job_req, job_pref)
    assert pytest.approx(res_half["score"], 0.001) == 0.50
    assert res_half["required_score"] == 0.0
    assert pytest.approx(res_half["preferred_score"], 0.001) == 0.50


def test_skill_match_categories_edge_cases():
    """Test required-only, preferred-only, and empty-skill cases."""
    # Required only
    res_req = calculate_skill_match_score(["Python"], ["Python", "SQL"], [])
    assert pytest.approx(res_req["score"], 0.001) == 0.50
    assert res_req["has_job_skills"] is True

    # Preferred only
    res_pref = calculate_skill_match_score(["Python"], [], ["Python", "SQL"])
    assert pytest.approx(res_pref["score"], 0.001) == 0.50
    assert res_pref["has_job_skills"] is True

    # Neither
    res_empty = calculate_skill_match_score(["Python"], [], [])
    assert res_empty["score"] == 0.0
    assert res_empty["has_job_skills"] is False


def test_weight_validation_and_normalization():
    """Test weight validation, normalization, and invalid fallback handling."""
    from matcher import validate_and_normalize_weights
    import math

    # Standard valid
    w_t, w_s, warn = validate_and_normalize_weights(0.65, 0.35)
    assert pytest.approx(w_t, 0.001) == 0.65
    assert pytest.approx(w_s, 0.001) == 0.35
    assert warn is None

    # Valid un-normalized (1.0, 3.0 -> 0.25, 0.75)
    w_t, w_s, warn = validate_and_normalize_weights(1.0, 3.0)
    assert pytest.approx(w_t, 0.001) == 0.25
    assert pytest.approx(w_s, 0.001) == 0.75

    # Negative weights -> fallback to defaults
    w_t, w_s, warn = validate_and_normalize_weights(-0.5, 0.5)
    assert warn is not None
    assert pytest.approx(w_t + w_s, 0.001) == 1.0

    # NaN / Inf weights -> fallback to defaults
    w_t, w_s, warn = validate_and_normalize_weights(float("nan"), 0.5)
    assert warn is not None
    assert math.isfinite(w_t) and math.isfinite(w_s)

    # Both zero -> fallback to defaults
    w_t, w_s, warn = validate_and_normalize_weights(0.0, 0.0)
    assert warn is not None
    assert pytest.approx(w_t + w_s, 0.001) == 1.0


def test_failed_extractions_score_zero_and_rank_last():
    """Ensure unparseable resumes always receive 0 scores and are placed at the bottom."""
    jd = "Senior Python engineer with AWS"
    resumes = [
        {"filename": "failed1.pdf", "success": False, "error": "Corrupt file"},
        {"filename": "good.txt", "success": True, "raw_text": "Python engineer with AWS experience"},
        {"filename": "failed2.pdf", "success": False, "error": "Password protected"}
    ]
    ranked = rank_resumes(jd, resumes)
    assert len(ranked) == 3
    assert ranked[0]["filename"] == "good.txt"
    assert ranked[0]["overall_score"] > 0.0
    assert ranked[1]["success"] is False
    assert ranked[1]["overall_score"] == 0.0
    assert ranked[2]["success"] is False
    assert ranked[2]["overall_score"] == 0.0


def test_end_to_end_extraction_failures_and_empty_resumes():
    """
    Test end-to-end parsing failures (corrupt PDF, empty file, unsupported extension)
    through parse_resume and verify rank_resumes ranks them at the bottom with 0.0 scores.
    """
    from resume_parser import parse_resume

    # 1. Corrupt PDF bytes
    corrupt_pdf = parse_resume(b"%PDF-1.4 corrupt content", "bad.pdf")
    assert corrupt_pdf["success"] is False
    assert "error" in corrupt_pdf

    # 2. Empty text file
    empty_txt = parse_resume(b"", "empty.txt")
    assert empty_txt["success"] is False

    # 3. Unsupported extension
    unsupported = parse_resume(b"\xff\xd8\xff", "photo.jpg")
    assert unsupported["success"] is False

    # 4. Valid resume
    valid_bytes = b"Jane Doe\njane@example.com\n555-0100\nSenior Python engineer with Docker, AWS, and PostgreSQL with extensive background."
    valid_resume = parse_resume(valid_bytes, "valid.txt")
    assert valid_resume["success"] is True

    # Rank all together
    jd = "Python Engineer with Docker and AWS"
    ranked = rank_resumes(jd, [corrupt_pdf, empty_txt, unsupported, valid_resume])

    assert len(ranked) == 4
    # The valid resume MUST be rank 1 with score > 0
    assert ranked[0]["filename"] == "valid.txt"
    assert ranked[0]["success"] is True
    assert ranked[0]["overall_score"] > 0.0

    # All three failures must be below the valid resume with 0.0 score
    for failed_cand in ranked[1:]:
        assert failed_cand["success"] is False
        assert failed_cand["overall_score"] == 0.0
        assert failed_cand["text_similarity_score"] == 0.0
        assert failed_cand["skill_match_score"] == 0.0
