"""
Tests for Fairness and Responsible Screening Safeguards
Covers:
- Proving that candidate names, email addresses, phone numbers, and filenames
  do NOT influence matching scores for identical resume content.
- Ensuring deterministic, transparent, identifier-independent ranking.
"""

import pytest
from matcher import rank_resumes


def test_fairness_identical_content_different_names():
    jd = """
    Role: Backend Developer
    Requirements:
    - 3+ years experience with Python and PostgreSQL
    - Good understanding of Docker and REST APIs
    """

    body = """
    Professional Experience:
    Software Engineer at Acme Inc
    - Developed backend services using Python and REST APIs.
    - Managed relational data schemas in PostgreSQL and deployed via Docker.
    """

    r1 = {
        "filename": "applicant_a.pdf",
        "name": "Alice Johnson",
        "emails": ["alice.johnson@example.com"],
        "phones": ["555-0100"],
        "success": True,
        "raw_text": f"Alice Johnson\nalice.johnson@example.com\n555-0100\n{body}"
    }

    r2 = {
        "filename": "applicant_b.docx",
        "name": "Bob Smith",
        "emails": ["bob.smith@example.org"],
        "phones": ["555-0200"],
        "success": True,
        "raw_text": f"Bob Smith\nbob.smith@example.org\n555-0200\n{body}"
    }

    r3 = {
        "filename": "applicant_c.txt",
        "name": "Devi Sharma",
        "emails": ["devi.sharma@example.in"],
        "phones": ["+91 98765 43210"],
        "success": True,
        "raw_text": f"Devi Sharma\ndevi.sharma@example.in\n+91 98765 43210\n{body}"
    }

    ranked = rank_resumes(jd, [r1, r2, r3])

    # All three candidates must have the exact same skill match score
    assert ranked[0]["skill_match_score"] == ranked[1]["skill_match_score"] == ranked[2]["skill_match_score"]

    # Matched skills must be identical
    assert ranked[0]["matched_skills"] == ranked[1]["matched_skills"] == ranked[2]["matched_skills"]

    # Overall and text similarity scores must be 100% identical across all three candidates
    scores = [c["overall_score"] for c in ranked]
    text_scores = [c["text_similarity_score"] for c in ranked]
    assert ranked[0]["overall_score"] == ranked[1]["overall_score"] == ranked[2]["overall_score"]
    assert ranked[0]["text_similarity_score"] == ranked[1]["text_similarity_score"] == ranked[2]["text_similarity_score"]
    assert max(scores) == min(scores)


def test_fairness_protected_attributes_not_in_skills():
    """Ensure demographic markers are never included in detected skills taxonomy."""
    from config import SKILL_TAXONOMY, ALIAS_TO_SKILL

    demographic_terms = [
        "male", "female", "man", "woman", "gender", "race", "black", "white",
        "asian", "hispanic", "latino", "christian", "muslim", "hindu", "jewish",
        "age", "young", "old", "married", "single", "disability", "caste"
    ]

    for term in demographic_terms:
        assert term not in ALIAS_TO_SKILL, f"Demographic term '{term}' must not be a skill alias!"
        assert term not in SKILL_TAXONOMY, f"Demographic term '{term}' must not be a canonical skill!"


def test_pii_removal_preserves_legitimate_skills():
    """
    Ensure strip_pii_for_matching does NOT remove legitimate skills or technical terms
    if a candidate's name happens to match a programming language (e.g., Ruby, Rust, Swift).
    """
    from matcher import strip_pii_for_matching, rank_resumes

    jd = "Seeking a developer experienced with Ruby and Swift."
    body = "Ruby Rose\nruby.rose@example.com\n555-0199\nExperienced with Ruby backend systems and Swift mobile apps."

    cleaned = strip_pii_for_matching(body, name="Ruby Rose", emails=["ruby.rose@example.com"], phones=["555-0199"])

    # "Ruby" and "Swift" must NOT be stripped from the body
    assert "ruby" in cleaned.lower()
    assert "swift" in cleaned.lower()

    # Verify ranking correctly captures both skills
    res = rank_resumes(jd, [{
        "filename": "ruby_dev.pdf",
        "name": "Ruby Rose",
        "emails": ["ruby.rose@example.com"],
        "phones": ["555-0199"],
        "success": True,
        "raw_text": body
    }])
    assert "Ruby" in res[0]["matched_skills"]
    assert "Swift" in res[0]["matched_skills"]
    assert res[0]["skill_match_score"] == 100.0


def test_tie_breaking_behavior_on_identical_scores():
    """
    Verify that candidates with identical substantive content receive identical scores,
    and that tie-breaking produces deterministic ordering without altering numerical scores.
    """
    jd = "Role: Cloud Engineer\nRequirements: AWS, Kubernetes, Terraform"
    body = "Experience: Managed AWS infrastructure with Kubernetes and Terraform."

    c1 = {
        "filename": "cand_a.pdf",
        "name": "Alex Candidate",
        "emails": ["alex@corp.com"],
        "phones": ["111-222-3333"],
        "success": True,
        "raw_text": f"Alex Candidate\nalex@corp.com\n111-222-3333\n{body}"
    }
    c2 = {
        "filename": "cand_b.docx",
        "name": "Zoe Candidate",
        "emails": ["zoe@intl.ac.uk"],
        "phones": ["+44 20 7946 0991"],
        "success": True,
        "raw_text": f"Zoe Candidate\nzoe@intl.ac.uk\n+44 20 7946 0991\n{body}"
    }

    results = rank_resumes(jd, [c1, c2])

    # Scores must be 100% identical
    assert results[0]["overall_score"] == results[1]["overall_score"]
    assert results[0]["text_similarity_score"] == results[1]["text_similarity_score"]
    assert results[0]["skill_match_score"] == results[1]["skill_match_score"]

    # Deterministic ranking order is maintained
    results_repeat = rank_resumes(jd, [c1, c2])
    assert [r["candidate_id"] for r in results] == [r["candidate_id"] for r in results_repeat]


def test_pii_removal_does_not_over_remove_ordinary_words_in_projects():
    """
    Ensure candidates whose names are also ordinary English words (e.g., 'Will Price', 'Art Mark')
    do NOT have substantive project descriptions stripped of words like 'price', 'will', 'mark'.
    Also verifies identical substantive scores across candidates regardless of identity.
    """
    from matcher import strip_pii_for_matching, make_terms, rank_resumes

    jd = "Role: Financial Pricing Engineer\nRequirements: Python, Pricing models, PostgreSQL"

    resume_price = (
        "Will Price\n"
        "will.price@fintech.example.com\n"
        "+1 (555) 019-2834\n"
        "Professional Experience:\n"
        "- Senior Quantitative Developer specializing in Python and PostgreSQL.\n"
        "- Evaluated market price volatility and implemented dynamic pricing algorithms.\n"
        "- Coordinated with project leads to review budget grants and pricing elasticity."
    )

    resume_doe = (
        "Jane Doe\n"
        "jane.doe@global.example.org\n"
        "+44 20 7946 0123\n"
        "Professional Experience:\n"
        "- Senior Quantitative Developer specializing in Python and PostgreSQL.\n"
        "- Evaluated market price volatility and implemented dynamic pricing algorithms.\n"
        "- Coordinated with project leads to review budget grants and pricing elasticity."
    )

    cleaned_price = strip_pii_for_matching(
        resume_price,
        name="Will Price",
        emails=["will.price@fintech.example.com"],
        phones=["+1 (555) 019-2834"]
    )

    cleaned_doe = strip_pii_for_matching(
        resume_doe,
        name="Jane Doe",
        emails=["jane.doe@global.example.org"],
        phones=["+44 20 7946 0123"]
    )

    # 1. Substantive domain words 'price' and 'pricing' must be retained in project text
    terms_price = make_terms(cleaned_price)
    assert "price" in terms_price, "Substantive word 'price' was over-removed from project text!"
    assert "pricing" in terms_price, "Substantive word 'pricing' was over-removed from project text!"

    # 2. Both candidates must have identical substantive terms and identical scores
    assert make_terms(cleaned_price) == make_terms(cleaned_doe)

    results = rank_resumes(jd, [
        {
            "filename": "will_price.pdf",
            "name": "Will Price",
            "emails": ["will.price@fintech.example.com"],
            "phones": ["+1 (555) 019-2834"],
            "success": True,
            "raw_text": resume_price
        },
        {
            "filename": "jane_doe.docx",
            "name": "Jane Doe",
            "emails": ["jane.doe@global.example.org"],
            "phones": ["+44 20 7946 0123"],
            "success": True,
            "raw_text": resume_doe
        }
    ])

    assert results[0]["overall_score"] == results[1]["overall_score"]
    assert results[0]["text_similarity_score"] == results[1]["text_similarity_score"]
    assert results[0]["skill_match_score"] == results[1]["skill_match_score"]


