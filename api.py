"""
FastAPI Backend Service for AI Resume Screening System.
Exposes REST endpoints for resume screening, scoring, result retrieval, and CSV report export.
Integrates directly with pure-Python matcher and resume_parser engines.
"""

import os
import time
import uuid
import hashlib
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import (
    SUPPORTED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MIN_JOB_DESCRIPTION_CHARS,
    DEFAULT_WEIGHT_TEXT_SIMILARITY,
    DEFAULT_WEIGHT_SKILL_MATCH,
)
from resume_parser import parse_resume
from matcher import rank_resumes
from requirement_extractor import extract_job_title
from exporter import generate_candidates_csv

SAMPLE_JOB_DESCRIPTION = """Role: Java Full Stack Developer

Responsibilities:
- Design, build, and maintain high-performance microservices and secure REST APIs.
- Develop interactive web applications with modern frontend components and robust Java backend services.
- Collaborate with cross-functional Agile engineering teams using Git for version control.
- Design database schemas, write optimized queries, and manage persistence layers using MySQL and PostgreSQL.
- Implement CI/CD automation pipelines and deploy containerized services using Docker.

Required Qualifications & Skills:
- 3+ years of relevant software engineering experience in full stack application development.
- Strong proficiency in Java, Spring Boot, Microservices, and REST APIs.
- Solid hands-on experience with relational databases including MySQL and PostgreSQL.
- Proficient in version control using Git and collaborative Agile workflows.
- Experience with Docker containerization and build tools.
- Bachelor's degree in Computer Science, Information Technology, or a related technical field.

Preferred Qualifications:
- Experience with Kubernetes and AWS cloud deployments.
- Knowledge of Kafka event streaming and Redis caching.
- Familiarity with CI/CD automation tools like Jenkins or GitHub Actions.
"""

import json
import re
import sqlite3

SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{8,64}$")


def is_hosted_environment() -> bool:
    """Detect whether code is running on a managed cloud platform (Render, Railway, etc.)."""
    indicators = ("RENDER", "DYNO", "RAILWAY_STATIC_URL", "FLY_ALLOC_ID", "KUBERNETES_SERVICE_HOST")
    if any(os.getenv(k) for k in indicators):
        return True
    if os.getenv("IS_CLOUD", "").lower() in ("true", "1", "yes") or os.getenv("HOSTED_ENVIRONMENT", "").lower() in ("cloud", "production"):
        return True
    return False


def mask_database_url(url: Optional[str]) -> str:
    """Mask database connection string password to prevent credential leakage in logs."""
    if not url or not isinstance(url, str):
        return "None"
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", url)


def normalize_database_url(url: Optional[str]) -> Optional[str]:
    """Normalize PostgreSQL / Neon connection string and enforce TLS for remote endpoints."""
    if not url or not isinstance(url, str):
        return None
    clean = url.strip()
    if not clean:
        return None
    if clean.startswith("postgres://"):
        clean = clean.replace("postgres://", "postgresql://", 1)

    # For Neon and remote PostgreSQL hosts, ensure sslmode=require if not specified
    if "sslmode=" not in clean.lower():
        import urllib.parse
        try:
            parsed = urllib.parse.urlparse(clean)
            if parsed.hostname and parsed.hostname.lower() not in ("localhost", "127.0.0.1"):
                sep = "&" if "?" in clean else "?"
                clean = f"{clean}{sep}sslmode=require"
        except Exception:
            pass
    return clean


class ScreeningSessionStore:
    """In-memory cache with Neon PostgreSQL (production) or SQLite (local development) persistent storage
    and filesystem JSON backup for screening sessions.
    """

    def __init__(
        self,
        max_entries: int = 200,
        ttl_seconds: int = 86400,
        storage_dir: Optional[str] = None,
        db_path: Optional[str] = None,
        database_url: Optional[str] = None,
    ):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, float] = {}
        self.max_entries = max_entries
        self.ttl = ttl_seconds
        self.storage_dir = (
            storage_dir
            or os.getenv("SESSION_STORAGE_DIR")
            or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sessions")
        )
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
        except Exception:
            pass

        self.db_path = (
            db_path
            or os.getenv("SESSION_DB_PATH")
            or os.path.join(self.storage_dir, "sessions.db")
        )

        raw_db_url = database_url if database_url is not None else os.getenv("DATABASE_URL")
        self.database_url = normalize_database_url(raw_db_url)

        self.storage_backend = "postgresql" if self.database_url else "sqlite"
        self.is_durable = bool(self.database_url) or not is_hosted_environment()

        if is_hosted_environment() and not self.database_url:
            import logging
            logging.getLogger("uvicorn.error").warning(
                "DATABASE_URL not configured in hosted cloud environment! "
                "Screening sessions will be stored in ephemeral SQLite/filesystem and WILL NOT survive redeployments. "
                "Configure a Neon PostgreSQL DATABASE_URL for durable session persistence."
            )
            if os.getenv("REQUIRE_DURABLE_STORAGE", "").lower() in ("true", "1", "yes"):
                raise RuntimeError(
                    "Durable storage required by configuration (REQUIRE_DURABLE_STORAGE=true), "
                    "but DATABASE_URL is not set."
                )

        if self.database_url:
            init_ok = self._init_pg_db()
            if not init_ok:
                if os.getenv("REQUIRE_DURABLE_STORAGE", "").lower() in ("true", "1", "yes"):
                    raise RuntimeError(
                        f"Failed to connect to durable PostgreSQL storage at {mask_database_url(self.database_url)}."
                    )
                # Fallback to local SQLite if durable storage was not explicitly mandated
                self.storage_backend = "sqlite"
                self.is_durable = False
                self._init_sqlite_db()
        else:
            self._init_sqlite_db()

    @contextmanager
    def _pg_conn(self):
        """Context manager yielding an active PostgreSQL connection with automatic commit/rollback.
        Uses connect_timeout=15 to tolerate Neon serverless compute cold-starts.
        """
        import psycopg2
        conn = psycopg2.connect(self.database_url, connect_timeout=15)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_pg_db(self) -> bool:
        """Initialize PostgreSQL table and index for durable session persistence across redeployments."""
        try:
            with self._pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS screening_sessions (
                            screening_id VARCHAR(64) PRIMARY KEY,
                            data TEXT NOT NULL,
                            created_at DOUBLE PRECISION NOT NULL,
                            expires_at DOUBLE PRECISION NOT NULL
                        );
                        CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON screening_sessions(expires_at);
                    """)
            return True
        except Exception as e:
            import logging
            logging.getLogger("uvicorn.error").error(
                f"Failed to initialize PostgreSQL screening_sessions schema at {mask_database_url(self.database_url)}: {e}"
            )
            return False

    def _init_sqlite_db(self) -> None:
        """Initialize SQLite table and index for resilient local development session persistence."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS screening_sessions (
                        screening_id TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        expires_at REAL NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON screening_sessions(expires_at)")
                conn.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass

    def _get_file_path(self, screening_id: str) -> Optional[str]:
        if not SESSION_ID_PATTERN.match(screening_id):
            return None
        return os.path.join(self.storage_dir, f"{screening_id}.json")

    def store(self, screening_id: str, data: Dict[str, Any]) -> None:
        if not SESSION_ID_PATTERN.match(screening_id):
            return
        self.cleanup()
        if len(self.sessions) >= self.max_entries:
            oldest_id = min(self.timestamps, key=lambda k: self.timestamps[k])
            self.delete(oldest_id)
        now = time.time()
        created_at = float(data.get("timestamp", now))
        expires_at = created_at + self.ttl

        # 1. Store in memory cache
        self.sessions[screening_id] = data
        self.timestamps[screening_id] = created_at

        # 2. Store in persistent database: PostgreSQL (production) or SQLite (local)
        data_json = json.dumps(data)
        if self.database_url:
            try:
                with self._pg_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO screening_sessions (screening_id, data, created_at, expires_at)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (screening_id) DO UPDATE SET
                                data = EXCLUDED.data,
                                created_at = EXCLUDED.created_at,
                                expires_at = EXCLUDED.expires_at
                        """, (screening_id, data_json, created_at, expires_at))
            except Exception as e:
                import logging
                logging.getLogger("uvicorn.error").error(f"PostgreSQL store failed for {screening_id}: {e}")
        else:
            try:
                with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO screening_sessions (screening_id, data, created_at, expires_at) VALUES (?, ?, ?, ?)",
                        (screening_id, data_json, created_at, expires_at),
                    )
            except Exception:
                pass

        # 3. Store in filesystem JSON for backward-compatibility fallback
        fpath = self._get_file_path(screening_id)
        if fpath:
            try:
                temp_path = f"{fpath}.tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                os.replace(temp_path, fpath)
            except Exception:
                pass

    def get(self, screening_id: str) -> Optional[Dict[str, Any]]:
        if not SESSION_ID_PATTERN.match(screening_id):
            return None
        self.cleanup()

        # 1. Fast in-memory check
        data = self.sessions.get(screening_id)
        if data:
            return data

        now = time.time()

        # 2. Persistent storage check: PostgreSQL or SQLite
        if self.database_url:
            try:
                with self._pg_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT data, expires_at FROM screening_sessions WHERE screening_id = %s",
                            (screening_id,),
                        )
                        row = cur.fetchone()
                        if row:
                            data_str, expires_at = row
                            if now <= expires_at:
                                loaded = json.loads(data_str)
                                self.sessions[screening_id] = loaded
                                self.timestamps[screening_id] = loaded.get("timestamp", now)
                                return loaded
                            else:
                                self.delete(screening_id)
                                return None
            except Exception as e:
                import logging
                logging.getLogger("uvicorn.error").error(f"PostgreSQL get failed for {screening_id}: {e}")
        else:
            try:
                with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT data, expires_at FROM screening_sessions WHERE screening_id = ?",
                        (screening_id,),
                    )
                    row = cursor.fetchone()
                    if row:
                        data_str, expires_at = row
                        if now <= expires_at:
                            loaded = json.loads(data_str)
                            self.sessions[screening_id] = loaded
                            self.timestamps[screening_id] = loaded.get("timestamp", now)
                            return loaded
                        else:
                            self.delete(screening_id)
                            return None
            except Exception:
                pass

        # 3. Filesystem fallback
        fpath = self._get_file_path(screening_id)
        if fpath and os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                ts = loaded.get("timestamp", 0)
                if now - ts <= self.ttl:
                    self.sessions[screening_id] = loaded
                    self.timestamps[screening_id] = ts
                    return loaded
                else:
                    self.delete(screening_id)
            except Exception:
                pass
        return None

    def delete(self, screening_id: str) -> None:
        self.sessions.pop(screening_id, None)
        self.timestamps.pop(screening_id, None)
        if self.database_url:
            try:
                with self._pg_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM screening_sessions WHERE screening_id = %s", (screening_id,))
            except Exception:
                pass
        else:
            try:
                with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                    conn.execute("DELETE FROM screening_sessions WHERE screening_id = ?", (screening_id,))
            except Exception:
                pass
        fpath = self._get_file_path(screening_id)
        if fpath and os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass

    def cleanup(self) -> None:
        now = time.time()
        expired = [sid for sid, ts in self.timestamps.items() if now - ts > self.ttl]
        for sid in expired:
            self.delete(sid)
        if self.database_url:
            try:
                with self._pg_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM screening_sessions WHERE expires_at < %s", (now,))
            except Exception:
                pass
        else:
            try:
                with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                    conn.execute("DELETE FROM screening_sessions WHERE expires_at < ?", (now,))
            except Exception:
                pass


session_store = ScreeningSessionStore(max_entries=200, ttl_seconds=86400)
DB_PATH = session_store.db_path

app = FastAPI(
    title="AI Resume Screening System API",
    description="High-performance, explainable AI resume screening and ranking backend.",
    version="1.0.0",
)

# Configure CORS with environment override and production defaults
raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:8501,"
    "http://127.0.0.1:5173,http://127.0.0.1:3000,http://127.0.0.1:8501,"
    "https://ai-resume-screening-system-nu.vercel.app,"
    "https://ai-resume-screening-systems.streamlit.app",
)
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

if "*" in allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
def health():
    """Health check endpoint reporting service status and persistence durability."""
    return {
        "status": "ok",
        "service": "ai-resume-screening-api",
        "version": "1.0.0",
        "storage_backend": session_store.storage_backend,
        "durable": session_store.is_durable,
    }


@app.get("/api/sample-jd")
def get_sample_job_description():
    """Returns sample job description template for quick testing."""
    return {
        "sample_job_description": SAMPLE_JOB_DESCRIPTION.strip(),
        "title": "Java Full Stack Developer",
    }


@app.post("/api/screen", status_code=status.HTTP_200_OK)
async def screen_resumes(
    job_description: str = Form(...),
    files: List[UploadFile] = File(...),
    weight_text_sim: float = Form(DEFAULT_WEIGHT_TEXT_SIMILARITY),
    weight_skill_match: float = Form(DEFAULT_WEIGHT_SKILL_MATCH),
):
    """
    Parse uploaded candidate resumes and screen against the provided job description.
    Computes text similarity, skill overlap, and evidence coverage.
    """
    jd_clean = (job_description or "").strip()
    if len(jd_clean) < MIN_JOB_DESCRIPTION_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job description must be at least {MIN_JOB_DESCRIPTION_CHARS} characters.",
        )

    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one resume file must be uploaded.",
        )

    parsed_resumes: List[Dict[str, Any]] = []

    for file in files:
        filename = file.filename or "unknown_resume"
        try:
            file_bytes = await file.read()
        except Exception as e:
            file_bytes = b""

        # Compute document identity hash
        doc_id = hashlib.sha256(file_bytes).hexdigest()[:16]

        # Parse the document using existing pure-Python parser
        parsed = parse_resume(file_bytes, filename)
        parsed["doc_id"] = doc_id
        parsed_resumes.append(parsed)

    # Rank resumes using existing scoring engine
    ranked = rank_resumes(
        job_description=jd_clean,
        parsed_resumes=parsed_resumes,
        weight_text_sim=weight_text_sim,
        weight_skill_match=weight_skill_match,
    )

    job_title = extract_job_title(jd_clean)
    screening_id = str(uuid.uuid4())

    candidates_count = len(ranked)
    successful_count = sum(1 for c in ranked if c.get("success"))
    failed_count = candidates_count - successful_count

    top_cand = ranked[0] if ranked else None
    top_name = (top_cand.get("name") or top_cand.get("filename")) if top_cand else None
    top_score = top_cand.get("overall_score", 0.0) if top_cand else 0.0
    avg_score = round(sum(c.get("overall_score", 0.0) for c in ranked) / max(1, candidates_count), 2)

    response_payload = {
        "screening_id": screening_id,
        "job_title": job_title,
        "job_description": jd_clean,
        "candidates_count": candidates_count,
        "summary": {
            "total_candidates": candidates_count,
            "successful_screened": successful_count,
            "failed_screened": failed_count,
            "top_candidate": top_name,
            "top_score": top_score,
            "average_score": avg_score,
        },
        "results": ranked,
        "weights": {
            "text_similarity": weight_text_sim,
            "skill_match": weight_skill_match,
        },
        "timestamp": time.time(),
    }

    session_store.store(screening_id, response_payload)
    return response_payload


@app.get("/api/screening/{screening_id}")
def get_screening_results(screening_id: str, response: Response):
    """Retrieve previously calculated screening results by screening_id."""
    if not SESSION_ID_PATTERN.match(screening_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid screening session ID format: '{screening_id}'.",
        )
    data = session_store.get(screening_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening session '{screening_id}' not found or has expired.",
        )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    return data


@app.get("/api/screening/{screening_id}/export")
def export_screening_csv(screening_id: str):
    """Export screening results to sanitized CSV format."""
    if not SESSION_ID_PATTERN.match(screening_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid screening session ID format: '{screening_id}'.",
        )
    data = session_store.get(screening_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening session '{screening_id}' not found or has expired.",
        )

    results = data.get("results", [])
    csv_text = generate_candidates_csv(results)
    safe_filename = f"screening_report_{screening_id[:8]}.csv"

    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
        },
    )
