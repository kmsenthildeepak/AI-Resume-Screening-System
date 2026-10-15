"""
Unit and Integration Tests for FastAPI Backend Service (api.py).
Tests REST endpoints, payload validation, candidate ranking, session retrieval, and CSV export.
"""

import io
import pytest
from fastapi.testclient import TestClient

from api import app, session_store, SAMPLE_JOB_DESCRIPTION


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-resume-screening-api"
    assert "version" in data


def test_get_sample_jd(client):
    response = client.get("/api/sample-jd")
    assert response.status_code == 200
    data = response.json()
    assert "sample_job_description" in data
    assert len(data["sample_job_description"]) > 50
    assert "Java" in data["title"] or "Developer" in data["title"]


def test_screen_resumes_short_jd_validation_fails(client):
    response = client.post(
        "/api/screen",
        data={"job_description": "Too short"},
        files=[("files", ("resume.txt", io.BytesIO(b"Some text"), "text/plain"))],
    )
    assert response.status_code == 400
    assert "at least 30 characters" in response.json()["detail"]


def test_screen_resumes_end_to_end_ranking(client):
    resume_1 = (
        "Alice Smith\nEmail: alice@example.com\n"
        "Senior Java Developer with 5 years experience in Spring Boot, Microservices, Docker, and REST APIs."
    )
    resume_2 = (
        "Bob Jones\nEmail: bob@example.com\n"
        "Graphic Designer with skills in Adobe Photoshop, Illustrator, and digital painting."
    )

    files = [
        ("files", ("alice_resume.txt", io.BytesIO(resume_1.encode("utf-8")), "text/plain")),
        ("files", ("bob_resume.txt", io.BytesIO(resume_2.encode("utf-8")), "text/plain")),
    ]

    response = client.post(
        "/api/screen",
        data={"job_description": SAMPLE_JOB_DESCRIPTION},
        files=files,
    )

    assert response.status_code == 200
    data = response.json()
    assert "screening_id" in data
    assert data["candidates_count"] == 2
    assert len(data["results"]) == 2

    # Alice (Java Dev) must outrank Bob (Graphic Designer)
    alice = data["results"][0]
    bob = data["results"][1]

    assert "alice" in alice["filename"].lower()
    assert alice["rank"] == 1
    assert alice["overall_score"] > bob["overall_score"]
    assert "Java" in alice["matched_skills"] or "Spring Boot" in alice["matched_skills"]

    # Verify session retrieval endpoint
    session_id = data["screening_id"]
    get_res = client.get(f"/api/screening/{session_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["screening_id"] == session_id
    assert len(retrieved["results"]) == 2


def test_get_nonexistent_screening_session_returns_404(client):
    response = client.get("/api/screening/nonexistent-session-id-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_export_screening_csv_endpoint(client):
    resume_text = (
        "Carol Danvers\nSenior Java and Spring Boot Engineer.\n"
        "Proficient in Docker, Microservices, and MySQL."
    )
    files = [
        ("files", ("carol.txt", io.BytesIO(resume_text.encode("utf-8")), "text/plain")),
    ]

    post_res = client.post(
        "/api/screen",
        data={"job_description": SAMPLE_JOB_DESCRIPTION},
        files=files,
    )
    assert post_res.status_code == 200
    screening_id = post_res.json()["screening_id"]

    # Fetch CSV export
    csv_res = client.get(f"/api/screening/{screening_id}/export")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert f"screening_report_{screening_id[:8]}.csv" in csv_res.headers["content-disposition"]
    csv_content = csv_res.text
    assert "Rank" in csv_content
    assert "Candidate ID" in csv_content
    assert "carol.txt" in csv_content


def test_screen_with_corrupted_file_and_valid_file(client):
    valid_resume = "David Miller\nJava, Spring Boot, Git, Docker developer."
    corrupted_pdf = b"%PDF-1.4 Corrupted content that will not parse properly"

    files = [
        ("files", ("david.txt", io.BytesIO(valid_resume.encode("utf-8")), "text/plain")),
        ("files", ("corrupted.pdf", io.BytesIO(corrupted_pdf), "application/pdf")),
    ]

    response = client.post(
        "/api/screen",
        data={"job_description": SAMPLE_JOB_DESCRIPTION},
        files=files,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["candidates_count"] == 2
    # David should be rank 1 with success=True
    assert data["results"][0]["filename"] == "david.txt"
    assert data["results"][0]["success"] is True
    assert data["results"][0]["overall_score"] > 0
    # Corrupted should be rank 2 with success=False
    assert data["results"][1]["filename"] == "corrupted.pdf"
    assert data["results"][1]["success"] is False
    assert data["results"][1]["overall_score"] == 0.0


def test_session_store_ttl_and_capacity():
    from api import ScreeningSessionStore

    store = ScreeningSessionStore(max_entries=2, ttl_seconds=1)
    store.store("session_001", {"val": 1})
    store.store("session_002", {"val": 2})
    assert store.get("session_001") is not None
    assert store.get("session_002") is not None

    # Adding a 3rd should evict oldest (session_001)
    store.store("session_003", {"val": 3})
    assert store.get("session_001") is None
    assert store.get("session_003") is not None


def test_screen_empty_files_returns_400(client):
    response = client.post(
        "/api/screen",
        data={"job_description": SAMPLE_JOB_DESCRIPTION},
        files=[],
    )
    # FastAPI returns 400 or 422 if files field is missing
    assert response.status_code in (400, 422)


def test_screen_four_sample_resumes_root_cause_regression(client):
    """
    Regression test for the 4 sample resumes:
    Ensures all 4 documents (TXT, DOCX, PDF) parse, score, and rank correctly,
    and validates that skill_evidence objects have the expected dictionary shape
    with snippets lists, tier strings, and boolean flags.
    """
    import os

    sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_resumes")
    resume_filenames = [
        "resume_01_strong_match.txt",
        "resume_02_partial_match.docx",
        "resume_03_unrelated.txt",
        "resume_04_python_dev.pdf",
    ]

    files = []
    opened_files = []
    try:
        for fname in resume_filenames:
            fpath = os.path.join(sample_dir, fname)
            f = open(fpath, "rb")
            opened_files.append(f)
            files.append(("files", (fname, f, "application/octet-stream")))

        response = client.post(
            "/api/screen",
            data={"job_description": SAMPLE_JOB_DESCRIPTION},
            files=files,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["candidates_count"] == 4
        assert len(data["results"]) == 4

        # Verify summary stats
        summary = data["summary"]
        assert summary["total_candidates"] == 4
        assert summary["successful_screened"] == 4
        assert summary["failed_screened"] == 0
        assert summary["top_score"] > 50.0

        # Verify rank 1 candidate
        top = data["results"][0]
        assert top["rank"] == 1
        assert top["overall_score"] > 50.0

        # Critical regression check for skill_evidence shape
        # In the bug, candidate.skill_evidence values are dicts, which crashed quotes.slice()
        # Verify that all candidates with matched skills have valid dicts with snippets lists
        for cand in data["results"]:
            skill_ev = cand.get("skill_evidence", {})
            assert isinstance(skill_ev, dict)
            for skill_name, ev_data in skill_ev.items():
                assert isinstance(ev_data, dict)
                assert "snippets" in ev_data
                assert isinstance(ev_data["snippets"], list)
                assert "tier" in ev_data
                assert "is_demonstrated" in ev_data
                assert isinstance(ev_data["is_demonstrated"], bool)

    finally:
        for f in opened_files:
            f.close()


def test_fetch_screening_session_valid_and_filesystem_fallback():
    """Verify fetch_screening_session retrieves from in-memory and from disk when cache cleared."""
    import time
    from app import fetch_screening_session

    test_id = "test-session-uuid-12345678"
    mock_payload = {
        "screening_id": test_id,
        "job_title": "Senior Python Architect",
        "job_description": "We need a Senior Python Architect with FastAPI experience.",
        "candidates_count": 1,
        "results": [
            {
                "candidate_id": "cand_01",
                "filename": "candidate_01.pdf",
                "overall_score": 88.5,
                "rank": 1,
            }
        ],
        "weights": {"text_similarity": 0.6, "skill_match": 0.4},
        "timestamp": time.time(),
    }

    # Store in session store (which also writes to .sessions/{test_id}.json)
    session_store.store(test_id, mock_payload)

    # 1. In-memory / direct fetch
    data, err = fetch_screening_session(test_id)
    assert err is None
    assert data is not None
    assert data["screening_id"] == test_id
    assert data["job_title"] == "Senior Python Architect"

    # 2. Clear in-memory session to force disk fallback
    session_store.sessions.clear()
    session_store.timestamps.clear()

    disk_data, disk_err = fetch_screening_session(test_id)
    assert disk_err is None
    assert disk_data is not None
    assert disk_data["screening_id"] == test_id
    assert len(disk_data["results"]) == 1

    # Cleanup
    session_store.delete(test_id)


def test_fetch_screening_session_invalid_format_and_path_traversal():
    """Verify malformed session IDs and path-traversal attempts are rejected safely."""
    from app import fetch_screening_session

    invalid_ids = [
        "",
        "short",
        "../../etc/passwd",
        "../app.py",
        "invalid session id with spaces",
        "semi;colon;drop",
        "<script>alert(1)</script>",
        "a" * 65,  # Exceeds 64 chars
    ]

    for bad_id in invalid_ids:
        data, err = fetch_screening_session(bad_id)
        assert data is None
        assert err is not None
        assert ("Invalid" in err or "No session ID" in err)


def test_fetch_screening_session_nonexistent_and_expired():
    """Verify non-existent and expired sessions return clear error messages."""
    import time
    from app import fetch_screening_session

    # Non-existent
    data, err = fetch_screening_session("nonexistent-valid-id-999999")
    assert data is None
    assert err is not None
    assert "not found" in err.lower()

    # Expired session
    expired_id = "expired-session-id-12345678"
    expired_payload = {
        "screening_id": expired_id,
        "job_title": "Old Job",
        "job_description": "Old JD",
        "candidates_count": 0,
        "results": [],
        "timestamp": time.time() - 100000,  # > 24 hours ago
    }
    session_store.store(expired_id, expired_payload)

    # Invalidate in-memory so it checks file TTL
    session_store.sessions.clear()
    session_store.timestamps.clear()

    exp_data, exp_err = fetch_screening_session(expired_id)
    assert exp_data is None
    assert exp_err is not None
    assert "expired" in exp_err.lower()

    # Cleanup
    session_store.delete(expired_id)

