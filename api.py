"""
FastAPI Backend Service for AI Resume Screening System.
Exposes REST endpoints for resume screening, scoring, result retrieval, and CSV report export.
Integrates directly with pure-Python matcher and resume_parser engines.
"""

import os
import time
import uuid
import hashlib
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

SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{8,64}$")


class ScreeningSessionStore:
    """In-memory cache with filesystem persistence, TTL and capacity limit for screening sessions."""

    def __init__(self, max_entries: int = 200, ttl_seconds: int = 86400, storage_dir: Optional[str] = None):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, float] = {}
        self.max_entries = max_entries
        self.ttl = ttl_seconds
        self.storage_dir = storage_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sessions")
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
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
        self.sessions[screening_id] = data
        self.timestamps[screening_id] = now

        # Write to filesystem for multi-process sharing with Streamlit
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
        data = self.sessions.get(screening_id)
        if data:
            return data

        # Filesystem fallback
        fpath = self._get_file_path(screening_id)
        if fpath and os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                ts = loaded.get("timestamp", 0)
                if time.time() - ts <= self.ttl:
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


session_store = ScreeningSessionStore(max_entries=200, ttl_seconds=86400)

app = FastAPI(
    title="AI Resume Screening System API",
    description="High-performance, explainable AI resume screening and ranking backend.",
    version="1.0.0",
)

# Configure CORS with environment override
raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000,https://ai-resume-screening-system-nu.vercel.app",
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
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "ai-resume-screening-api",
        "version": "1.0.0",
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
def get_screening_results(screening_id: str):
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
            "Cache-Control": "no-cache",
        },
    )
