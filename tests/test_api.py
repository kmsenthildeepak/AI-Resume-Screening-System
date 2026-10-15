"""
Unit and Integration Tests for FastAPI Backend Service (api.py).
Tests REST endpoints, payload validation, candidate ranking, session retrieval, and CSV export.
"""

import io
import os
import time
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


def test_is_safe_api_url_validation():
    """Verify is_safe_api_url allows valid hosts and blocks SSRF / private targets."""
    from app import is_safe_api_url

    # Safe URLs
    assert is_safe_api_url("http://localhost:8000") is True
    assert is_safe_api_url("http://127.0.0.1:8000") is True
    assert is_safe_api_url("https://ai-resume-screening-system-usr9.onrender.com") is True
    assert is_safe_api_url("https://api.mycompany.com/screening") is True

    # Unsafe / Dangerous / Malformed URLs
    assert is_safe_api_url("") is False
    assert is_safe_api_url(None) is False
    assert is_safe_api_url("ftp://malicious.com") is False
    assert is_safe_api_url("file:///etc/passwd") is False
    assert is_safe_api_url("http://insecure-remote.com") is False  # HTTP remote disallowed
    assert is_safe_api_url("https://user:password@malicious.com") is False  # Credentials disallowed
    assert is_safe_api_url("https://169.254.169.254/latest/meta-data") is False  # Cloud metadata
    assert is_safe_api_url("https://metadata.google.internal") is False  # GCP metadata
    assert is_safe_api_url("https://192.168.1.100") is False  # Private IP range
    assert is_safe_api_url("https://10.0.0.1") is False  # Private IP range
    assert is_safe_api_url("https://172.16.0.1") is False  # Private IP range


def test_resolve_api_base_url_hierarchy(monkeypatch):
    """Verify resolve_api_base_url adheres to strict trust hierarchy and blocks hosted query hijacking."""
    from app import resolve_api_base_url, DEFAULT_PRODUCTION_API_URL, DEFAULT_LOCAL_API_URL

    # Ensure clean slate for cloud indicators
    monkeypatch.delenv("STREAMLIT_HOST", raising=False)
    monkeypatch.delenv("STREAMLIT_SHARING", raising=False)
    monkeypatch.delenv("STREAMLIT_COMMUNITY_CLOUD", raising=False)
    monkeypatch.delenv("STREAMLIT_SERVER_BASE_URL", raising=False)
    monkeypatch.delenv("KUBERNETES_SERVICE_HOST", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("IS_CLOUD", raising=False)
    monkeypatch.delenv("API_BASE_URL", raising=False)

    # 1. Local development: query parameter allowed for local overrides
    custom_local_url = "http://localhost:8001"
    resolved = resolve_api_base_url(query_api_url=custom_local_url)
    assert resolved == custom_local_url

    # 2. Local development fallback to default 8000
    assert resolve_api_base_url() == DEFAULT_LOCAL_API_URL

    # 3. Environment variable takes precedence over local query param
    monkeypatch.setenv("API_BASE_URL", "https://env-backend.onrender.com")
    assert resolve_api_base_url(query_api_url=custom_local_url) == "https://env-backend.onrender.com"

    # 4. Hosted cloud ignores user-supplied query parameter overrides
    monkeypatch.setenv("STREAMLIT_HOST", "streamlit.app")
    untrusted_query = "https://untrusted-backend.onrender.com"
    # When API_BASE_URL is set, hosted cloud uses it and ignores query param
    assert resolve_api_base_url(query_api_url=untrusted_query) == "https://env-backend.onrender.com"

    # When API_BASE_URL is absent in hosted cloud, falls back to fixed trusted production URL
    monkeypatch.delenv("API_BASE_URL", raising=False)
    assert resolve_api_base_url(query_api_url=untrusted_query) == DEFAULT_PRODUCTION_API_URL


def test_hosted_streamlit_ignores_untrusted_query_api_url(monkeypatch):
    """Ensure hosted Streamlit trusts configured secrets/env or default prod URL over attacker query params."""
    from app import resolve_api_base_url, DEFAULT_PRODUCTION_API_URL

    monkeypatch.setenv("STREAMLIT_COMMUNITY_CLOUD", "true")
    monkeypatch.setenv("API_BASE_URL", "https://trusted-production-api.onrender.com")

    attacker_query = "https://attacker-controlled-api.onrender.com"
    resolved = resolve_api_base_url(query_api_url=attacker_query)

    assert resolved == "https://trusted-production-api.onrender.com"
    assert resolved != attacker_query


def test_sqlite_persistence_and_cache_control_headers(client):
    """Verify session is written to SQLite and API endpoints set strict no-cache headers."""
    import sqlite3
    from api import DB_PATH

    res = client.get("/api/sample-jd")
    assert res.status_code == 200

    test_res_data = {
        "screening_id": "sqlite-test-sess-12345678",
        "job_title": "Test Engineer",
        "job_description": "Test JD requirements",
        "candidates_count": 1,
        "results": [],
        "timestamp": time.time(),
    }
    session_store.store(test_res_data["screening_id"], test_res_data)

    # Check SQLite record exists
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT screening_id FROM screening_sessions WHERE screening_id = ?", (test_res_data["screening_id"],))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == test_res_data["screening_id"]

    # Verify Cache-Control headers on retrieval
    resp = client.get(f"/api/screening/{test_res_data['screening_id']}")
    assert resp.status_code == 200
    assert "no-store" in resp.headers.get("Cache-Control", "")
    assert resp.headers.get("Pragma") == "no-cache"

    # Cleanup
    session_store.delete(test_res_data["screening_id"])


def test_fetch_screening_session_handles_network_timeout(monkeypatch):
    """Verify fetch_screening_session returns informative message on connection timeout."""
    import urllib.error
    from app import fetch_screening_session

    def mock_urlopen_timeout(*args, **kwargs):
        raise urllib.error.URLError("timed out")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen_timeout)

    # Clear in-memory & file/sqlite caches to force network fetch
    test_id = "test-timeout-session-id-123456"
    data, err = fetch_screening_session(test_id, query_api_url="https://ai-resume-screening-system-usr9.onrender.com")
    assert data is None
    assert err is not None
    assert "timed out" in err.lower() or "waking from sleep" in err.lower()


class MockPgCursor:
    """Mock psycopg2 cursor implementing parameterized SQL queries for session store."""

    def __init__(self, db_store):
        self.db = db_store
        self._current_row = None

    def execute(self, sql, params=None):
        sql_clean = " ".join(sql.strip().split())
        sql_upper = sql_clean.upper()

        if "CREATE TABLE" in sql_upper or "CREATE INDEX" in sql_upper:
            return
        if "INSERT INTO SCREENING_SESSIONS" in sql_upper:
            # (screening_id, data, created_at, expires_at)
            sid, data_json, created_at, expires_at = params
            self.db[sid] = (data_json, expires_at)
        elif "SELECT DATA, EXPIRES_AT FROM SCREENING_SESSIONS" in sql_upper:
            sid = params[0]
            self._current_row = self.db.get(sid)
        elif "DELETE FROM SCREENING_SESSIONS WHERE SCREENING_ID" in sql_upper:
            sid = params[0]
            self.db.pop(sid, None)
        elif "DELETE FROM SCREENING_SESSIONS WHERE EXPIRES_AT <" in sql_upper:
            cutoff = params[0]
            for k in [k for k, v in self.db.items() if v[1] < cutoff]:
                self.db.pop(k, None)

    def fetchone(self):
        return self._current_row

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class MockPgConnection:
    """Mock psycopg2 connection object."""

    def __init__(self, db_store):
        self.db = db_store

    def cursor(self):
        return MockPgCursor(self.db)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def test_postgresql_storage_persistence_retrieval_and_export(monkeypatch, client):
    """Verify PostgreSQL-backed ScreeningSessionStore persists, retrieves after cache clear, and exports CSV."""
    import psycopg2
    from api import ScreeningSessionStore, app as api_app

    mock_db = {}

    def mock_pg_connect(*args, **kwargs):
        return MockPgConnection(mock_db)

    monkeypatch.setattr(psycopg2, "connect", mock_pg_connect)

    # Initialize store with PostgreSQL DATABASE_URL
    pg_url = "postgresql://user:pass@ep-render-test.render.com/resumes?sslmode=require"
    store = ScreeningSessionStore(database_url=pg_url)

    assert store.storage_backend == "postgresql"
    assert store.is_durable is True
    assert store.database_url == pg_url

    test_id = "pg-test-sess-98765432"
    test_payload = {
        "screening_id": test_id,
        "job_title": "Principal Distributed Systems Engineer",
        "job_description": "Deep PostgreSQL, Kubernetes, and Python expertise.",
        "candidates_count": 1,
        "summary": {
            "total_candidates": 1,
            "successful_screened": 1,
            "failed_screened": 0,
            "top_candidate": "Alice Postgres",
            "top_score": 95.0,
            "average_score": 95.0,
        },
        "results": [
            {
                "candidate_id": "cand_pg_01",
                "doc_id": "doc_pg_01",
                "filename": "alice_postgres.pdf",
                "name": "Alice Postgres",
                "emails": ["alice@pg.internal"],
                "phones": ["+1-555-0199"],
                "success": True,
                "error": None,
                "warning": None,
                "overall_score": 95.0,
                "text_similarity_score": 94.0,
                "skill_match_score": 96.0,
                "evidence_coverage_score": 95.0,
                "matched_skills": ["PostgreSQL", "Python", "Kubernetes"],
                "missing_skills": [],
                "candidate_skills": ["PostgreSQL", "Python", "Kubernetes", "Docker"],
                "skill_evidence": {},
                "education_evidence": [],
                "experience_evidence": [],
                "score_explanation": "Strong match across all core competency requirements.",
                "rank": 1,
            }
        ],
        "weights": {"text_similarity": 0.5, "skill_match": 0.5},
        "timestamp": time.time(),
    }

    # 1. Store in PostgreSQL
    store.store(test_id, test_payload)
    assert test_id in mock_db

    # 2. Clear in-memory cache to prove retrieval comes from PostgreSQL
    store.sessions.clear()
    store.timestamps.clear()

    # 3. Retrieve from PostgreSQL
    retrieved = store.get(test_id)
    assert retrieved is not None
    assert retrieved["screening_id"] == test_id
    assert retrieved["job_title"] == "Principal Distributed Systems Engineer"
    assert retrieved["results"][0]["name"] == "Alice Postgres"

    # Verify in-memory cache was re-populated
    assert test_id in store.sessions

    # 4. Attach store to FastAPI app and verify HTTP endpoints
    from api import session_store as global_session_store
    monkeypatch.setattr("api.session_store", store)

    get_resp = client.get(f"/api/screening/{test_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["screening_id"] == test_id

    # 5. Verify CSV export retrieves from PostgreSQL
    export_resp = client.get(f"/api/screening/{test_id}/export")
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["Content-Type"]
    assert "Alice Postgres" in export_resp.text
    assert "alice_postgres.pdf" in export_resp.text

    # 6. Verify TTL expiry in PostgreSQL
    expired_id = "pg-expired-session-12345678"
    expired_payload = dict(test_payload)
    expired_payload["screening_id"] = expired_id
    expired_payload["timestamp"] = time.time() - 100000  # Expired
    store.store(expired_id, expired_payload)

    store.sessions.clear()
    store.timestamps.clear()

    assert store.get(expired_id) is None
    assert expired_id not in mock_db


def test_missing_database_url_in_hosted_environment_reports_non_durable(monkeypatch):
    """Verify that in a hosted cloud environment without DATABASE_URL, store reports is_durable=False."""
    from api import ScreeningSessionStore

    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    store = ScreeningSessionStore(database_url=None)
    assert store.storage_backend == "sqlite"
    assert store.is_durable is False


def test_require_durable_storage_raises_without_database_url(monkeypatch):
    """Verify that REQUIRE_DURABLE_STORAGE=true fails fast if DATABASE_URL is missing."""
    import pytest
    from api import ScreeningSessionStore

    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("REQUIRE_DURABLE_STORAGE", "true")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        ScreeningSessionStore(database_url=None)
    assert "DATABASE_URL is not set" in str(exc_info.value)


def test_neon_database_url_normalization_and_tls_enforcement():
    """Verify Neon PostgreSQL connection strings enforce TLS (sslmode=require) and normalize scheme."""
    from api import normalize_database_url

    # 1. Neon URI with postgres:// prefix and missing sslmode
    neon_raw = "postgres://neondb_owner:npg_secret123@ep-silent-smoke-a5123456.us-east-2.aws.neon.tech/neondb"
    normalized = normalize_database_url(neon_raw)
    assert normalized.startswith("postgresql://")
    assert "sslmode=require" in normalized

    # 2. Neon URI already having sslmode=require
    neon_with_ssl = "postgresql://user:pass@ep-cool-fog.us-east-2.aws.neon.tech/neondb?sslmode=require"
    assert normalize_database_url(neon_with_ssl) == neon_with_ssl

    # 3. Localhost URI does not force sslmode
    local_url = "postgresql://postgres:postgres@localhost:5432/testdb"
    assert "sslmode" not in normalize_database_url(local_url)

    # 4. None / empty handling
    assert normalize_database_url(None) is None
    assert normalize_database_url("   ") is None


def test_mask_database_url_redacts_credentials():
    """Verify mask_database_url prevents passwords from leaking into logs or traces."""
    from api import mask_database_url

    neon_url = "postgresql://neondb_owner:SuperSecretPassword123!@ep-cold-start.neon.tech/neondb?sslmode=require"
    masked = mask_database_url(neon_url)

    assert "SuperSecretPassword123!" not in masked
    assert "neondb_owner:****@" in masked
    assert "ep-cold-start.neon.tech" in masked
    assert mask_database_url(None) == "None"


def test_postgresql_connection_failure_falls_back_when_not_required(monkeypatch):
    """Verify that connection failure falls back to SQLite with is_durable=False when not hard-mandated."""
    import psycopg2
    from api import ScreeningSessionStore

    def mock_failing_connect(*args, **kwargs):
        raise psycopg2.OperationalError("Could not connect to Neon server: connection timed out")

    monkeypatch.setattr(psycopg2, "connect", mock_failing_connect)
    monkeypatch.delenv("REQUIRE_DURABLE_STORAGE", raising=False)

    store = ScreeningSessionStore(database_url="postgresql://user:pass@ep-fail.neon.tech/db")
    assert store.storage_backend == "sqlite"
    assert store.is_durable is False


def test_require_durable_storage_raises_on_neon_connection_failure(monkeypatch):
    """Verify that REQUIRE_DURABLE_STORAGE=true fails fast with RuntimeError on database connection failure."""
    import pytest
    import psycopg2
    from api import ScreeningSessionStore

    def mock_failing_connect(*args, **kwargs):
        raise psycopg2.OperationalError("FATAL: password authentication failed for user 'neondb_owner'")

    monkeypatch.setattr(psycopg2, "connect", mock_failing_connect)
    monkeypatch.setenv("REQUIRE_DURABLE_STORAGE", "true")

    with pytest.raises(RuntimeError) as exc_info:
        ScreeningSessionStore(database_url="postgresql://neondb_owner:secret@ep-fail.neon.tech/db")
    assert "Failed to connect to durable PostgreSQL storage" in str(exc_info.value)
    assert "secret" not in str(exc_info.value)  # Ensure password was masked!


def test_local_dev_sqlite_fallback_when_database_url_absent(monkeypatch):
    """Verify local development uses SQLite and marks is_durable=True (locally durable on disk)."""
    from api import ScreeningSessionStore

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("IS_CLOUD", raising=False)
    monkeypatch.delenv("KUBERNETES_SERVICE_HOST", raising=False)
    monkeypatch.delenv("FLY_ALLOC_ID", raising=False)

    store = ScreeningSessionStore(database_url=None)
    assert store.storage_backend == "sqlite"
    assert store.is_durable is True


def test_postgresql_unavailable_after_startup_and_recovery(monkeypatch, client):
    """Verify that when PostgreSQL becomes unreachable after startup, in-memory cache
    still functions, failed DB queries do not crash or leak secrets, and recovery succeeds
    when the database becomes available again.
    """
    import psycopg2
    from api import ScreeningSessionStore

    mock_db = {}
    is_pg_online = True

    def toggleable_connect(*args, **kwargs):
        if not is_pg_online:
            raise psycopg2.OperationalError("server closed the connection unexpectedly")
        return MockPgConnection(mock_db)

    monkeypatch.setattr(psycopg2, "connect", toggleable_connect)

    # 1. Start up successfully
    pg_url = "postgresql://neondb_owner:npg_secret@ep-test.neon.tech/neondb?sslmode=require"
    store = ScreeningSessionStore(database_url=pg_url)
    assert store.storage_backend == "postgresql"

    test_id = "pg-recovery-sess-12345678"
    test_payload = {
        "screening_id": test_id,
        "job_title": "Platform Engineer",
        "job_description": "PostgreSQL reliability engineer",
        "candidates_count": 1,
        "results": [{"name": "Recovery Candidate", "overall_score": 88.0, "success": True}],
        "timestamp": time.time(),
    }

    # Store while DB is online
    store.store(test_id, test_payload)
    assert test_id in mock_db

    # 2. Simulate PostgreSQL outage after startup
    is_pg_online = False

    # In-memory retrieval still succeeds immediately without querying DB
    cached = store.get(test_id)
    assert cached is not None
    assert cached["job_title"] == "Platform Engineer"

    # Clear in-memory cache to force DB retrieval during outage
    store.sessions.clear()
    store.timestamps.clear()

    # During DB outage, local filesystem backup provides immediate fallback
    fallback_res = store.get(test_id)
    assert fallback_res is not None
    assert fallback_res["screening_id"] == test_id

    # If local filesystem was wiped (simulating container restart with DB still unreachable)
    fpath = store._get_file_path(test_id)
    if fpath and os.path.exists(fpath):
        os.remove(fpath)
    store.sessions.clear()
    store.timestamps.clear()

    # DB retrieval during outage catches error gracefully and returns None without crashing
    res_during_outage = store.get(test_id)
    assert res_during_outage is None

    # Storing a new session during DB outage still saves to in-memory cache without crashing
    new_id = "pg-outage-sess-87654321"
    new_payload = dict(test_payload, screening_id=new_id)
    store.store(new_id, new_payload)
    assert store.get(new_id) is not None

    # 3. Connection recovery: simulate PostgreSQL coming back online
    is_pg_online = True

    # Now previously stored DB session can be retrieved again from DB
    store.sessions.clear()
    store.timestamps.clear()
    recovered = store.get(test_id)
    assert recovered is not None
    assert recovered["screening_id"] == test_id

    # Cleanup test files
    store.delete(test_id)
    store.delete(new_id)

