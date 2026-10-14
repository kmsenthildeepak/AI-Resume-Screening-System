"""
Regression and unit tests for Resume Upload Queue Removal and Synchronization.

Test Architecture:
------------------
1. SECTION A: Genuine Streamlit Widget-Lifecycle Tests (using Streamlit AppTest)
   - Real file uploader widget interactions (upload, drop, clear, re-upload).
   - UI expander removal selectbox and button interactions.
   - Multiple consecutive reruns confirming removed documents stay removed.
   - Multipage ATS navigation confirming queue retention and removed document exclusion.
   - Same-filename different-content uploads and single document removal.
   - Clear Queue button testing complete session state reset.

2. SECTION B: Focused Unit Tests on Document Identity and Pruning Logic
   - Deterministic SHA-256 document ID computation and collision resistance.
   - prune_screening_results() primary identity matching (doc_id) vs legacy fallback (filename).
   - Rank re-indexing (#1..N) and selected candidate fallback upon removal.
"""

import hashlib
import os
import io
import csv
import pytest
from streamlit.testing.v1 import AppTest

from app import compute_document_id, prune_screening_results
from matcher import rank_resumes
from resume_parser import parse_resume
from exporter import generate_candidates_csv

SAMPLE_JD = """Role: Python Backend Engineer
Responsibilities:
- Build high-scale microservices and REST APIs using Python, FastAPI, and Django.
- Design database architectures with PostgreSQL and Redis caching.
- Deploy services using Docker, Kubernetes, and AWS CI/CD pipelines.

Required Qualifications:
- 3+ years experience with Python, FastAPI, or Django.
- Experience with PostgreSQL, Docker, and REST APIs.
- Collaborative version control with Git.
"""


# ==============================================================================
# SECTION A: GENUINE STREAMLIT WIDGET-LIFECYCLE TESTS (AppTest)
# ==============================================================================

def test_upload_two_resumes_and_remove_one_via_uploader():
    """[Widget-Lifecycle] Upload 2 resumes, remove 1 via uploader widget.

    Active queue must report exactly 1 candidate document.
    """
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    r1_bytes = b"Alice Walker\nEmail: alice@example.com\nSkills: Python, FastAPI, PostgreSQL, Docker"
    r2_bytes = b"Bob Martin\nEmail: bob@example.com\nSkills: Java, Spring Boot, MySQL"

    at.file_uploader[0].upload("alice_walker.txt", r1_bytes).upload("bob_martin.txt", r2_bytes).run()
    assert not at.exception

    # Queue must contain 2 candidate documents
    assert len(at.session_state["uploaded_resumes_cache"]) == 2
    queue_text_2 = " ".join(m.value for m in at.markdown)
    assert "✓ <strong>2</strong> candidate document(s) in active queue" in queue_text_2
    assert "alice_walker.txt" in queue_text_2
    assert "bob_martin.txt" in queue_text_2

    # Remove bob_martin.txt from uploader (simulating user clicking × in uploader)
    at.file_uploader[0].upload("alice_walker.txt", r1_bytes).run()
    assert not at.exception

    # Active queue must now strictly contain only alice_walker.txt
    assert len(at.session_state["uploaded_resumes_cache"]) == 1
    assert at.session_state["uploaded_resumes_cache"][0]["filename"] == "alice_walker.txt"

    queue_text_1 = " ".join(m.value for m in at.markdown)
    assert "✓ <strong>1</strong> candidate document(s) in active queue" in queue_text_1
    assert "alice_walker.txt" in queue_text_1
    assert "bob_martin.txt" not in queue_text_1


def test_upload_8_resumes_remove_2_and_screen_only_remaining_6():
    """[Widget-Lifecycle] Upload 8 resumes, remove 2 -> 6 remain.

    Click Analyze & Rank Candidates -> screens strictly the 6 active resumes.
    """
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    at.text_area(key="jd_textarea").input(SAMPLE_JD).run()

    candidates_data = [
        ("cand_01.txt", b"Candidate 1\nEmail: c1@test.com\nSkills: Python, FastAPI, Docker, PostgreSQL"),
        ("cand_02.txt", b"Candidate 2\nEmail: c2@test.com\nSkills: Python, Django, PostgreSQL"),
        ("cand_03.txt", b"Candidate 3\nEmail: c3@test.com\nSkills: Python, Docker, Redis"),
        ("cand_04.txt", b"Candidate 4\nEmail: c4@test.com\nSkills: Python, FastAPI, Git"),
        ("cand_05.txt", b"Candidate 5\nEmail: c5@test.com\nSkills: PostgreSQL, Redis, Docker"),
        ("cand_06.txt", b"Candidate 6\nEmail: c6@test.com\nSkills: Python, REST APIs"),
        ("cand_07.txt", b"Candidate 7\nEmail: c7@test.com\nSkills: Java, Spring Boot"),
        ("cand_08.txt", b"Candidate 8\nEmail: c8@test.com\nSkills: Sales, Marketing, HR")
    ]

    uploader = at.file_uploader[0]
    for fname, content in candidates_data:
        uploader.upload(fname, content)
    uploader.run()
    assert not at.exception

    assert len(at.session_state["uploaded_resumes_cache"]) == 8
    queue_text_8 = " ".join(m.value for m in at.markdown)
    assert "✓ <strong>8</strong> candidate document(s) in active queue" in queue_text_8

    # Now remove 2 files (cand_07.txt and cand_08.txt) by retaining only the first 6
    remaining_6 = candidates_data[:6]
    uploader_remaining = at.file_uploader[0]
    for fname, content in remaining_6:
        uploader_remaining.upload(fname, content)
    uploader_remaining.run()
    assert not at.exception

    # Verify active queue has strictly 6 resumes
    assert len(at.session_state["uploaded_resumes_cache"]) == 6
    filenames_in_cache = [c["filename"] for c in at.session_state["uploaded_resumes_cache"]]
    assert filenames_in_cache == ["cand_01.txt", "cand_02.txt", "cand_03.txt", "cand_04.txt", "cand_05.txt", "cand_06.txt"]
    assert "cand_07.txt" not in filenames_in_cache
    assert "cand_08.txt" not in filenames_in_cache

    queue_text_6 = " ".join(m.value for m in at.markdown)
    assert "✓ <strong>6</strong> candidate document(s) in active queue" in queue_text_6

    # Click Analyze & Rank Candidates
    analyze_btns = [b for b in at.button if "Analyze & Rank" in b.label]
    assert len(analyze_btns) == 1
    analyze_btns[0].click().run()
    assert not at.exception

    # Strictly 6 candidates evaluated and ranked
    results = at.session_state["screening_results"]
    assert len(results) == 6
    result_filenames = [c["filename"] for c in results]
    assert "cand_07.txt" not in result_filenames
    assert "cand_08.txt" not in result_filenames

    # Continuous ranks #1 through #6
    for idx, cand in enumerate(results, start=1):
        assert cand["rank"] == idx

    # Verify CSV export contains strictly 6 candidate rows + 1 header row
    csv_out = generate_candidates_csv(results)
    rows = list(csv.reader(io.StringIO(csv_out)))
    assert len(rows) == 7  # header + 6 data rows
    exported_files = [row[2] for row in rows[1:]]
    assert "cand_07.txt" not in exported_files
    assert "cand_08.txt" not in exported_files


def test_widget_custom_remove_button_survives_multiple_reruns():
    """[Widget-Lifecycle] Edge Case 1: After removing via Remove Selected Document button,

    trigger multiple reruns and verify stale uploader state cannot re-add the removed document.
    """
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    at.file_uploader[0].upload("r1.txt", b"Resume 1 Python Dev").upload("r2.txt", b"Resume 2 Java Dev").run()
    assert len(at.session_state["uploaded_resumes_cache"]) == 2

    # Remove r1 via the UI expander selectbox and button
    r1_id = [it["doc_id"] for it in at.session_state["uploaded_resumes_cache"] if it["filename"] == "r1.txt"][0]
    at.selectbox(key="sel_remove_single_resume").set_value(r1_id).run()

    rem_btns = [b for b in at.button if "Remove Selected Document" in b.label]
    assert len(rem_btns) == 1
    rem_btns[0].click().run()

    assert len(at.session_state["uploaded_resumes_cache"]) == 1
    assert at.session_state["uploaded_resumes_cache"][0]["filename"] == "r2.txt"

    # Trigger 5 consecutive reruns to verify stability
    for _ in range(5):
        at.run()
        cached = [it["filename"] for it in at.session_state["uploaded_resumes_cache"]]
        assert len(cached) == 1
        assert cached == ["r2.txt"]
        assert "r1.txt" not in cached


def test_first_run_branch_cannot_reingest_stale_selections_after_uploader_key_bump():
    """[Widget-Lifecycle] Edge Case 2: Verify that resetting uploader_known_doc_ids to None

    and bumping uploader_key prevents the first-run branch from re-ingesting removed items.
    """
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Upload docA and docB
    at.file_uploader[0].upload("docA.txt", b"Doc A content").upload("docB.txt", b"Doc B content").run()
    assert len(at.session_state["uploaded_resumes_cache"]) == 2

    # Remove docA via UI button (which bumps uploader_key and sets uploader_known_doc_ids = None)
    docA_id = [it["doc_id"] for it in at.session_state["uploaded_resumes_cache"] if it["filename"] == "docA.txt"][0]
    at.selectbox(key="sel_remove_single_resume").set_value(docA_id).run()
    rem_btns = [b for b in at.button if "Remove Selected Document" in b.label]
    rem_btns[0].click().run()

    # Verify docA is recorded in removed_doc_ids and not in uploaded_resumes_cache
    assert docA_id in at.session_state["removed_doc_ids"]
    assert len(at.session_state["uploaded_resumes_cache"]) == 1
    assert at.session_state["uploaded_resumes_cache"][0]["filename"] == "docB.txt"

    # Multiple reruns on the new uploader key
    for _ in range(3):
        at.run()
        assert len(at.session_state["uploaded_resumes_cache"]) == 1
        assert at.session_state["uploaded_resumes_cache"][0]["filename"] == "docB.txt"


def test_same_filename_different_bytes_removal_preserves_other_document():
    """[Widget-Lifecycle] Edge Cases 3 & 4: Upload two different resume files with the SAME filename

    but different bytes. Screen both, then remove one. Verify that ONLY its document ID is
    removed from the active queue and screening results, and the other candidate remains.
    """
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Set Job Description
    at.text_area(key="jd_textarea").input(SAMPLE_JD).run()

    b1 = b"Alice Walker\nEmail: alice@example.com\nSkills: Python, FastAPI, Docker, PostgreSQL\nExperience: Senior Engineer"
    b2 = b"Bob Martin\nEmail: bob@example.com\nSkills: Java, Spring Boot, MySQL\nExperience: Junior Developer"

    # Both uploaded files have the same filename: 'resume.txt'
    at.file_uploader[0].upload("resume.txt", b1).upload("resume.txt", b2).run()
    assert not at.exception

    # Document IDs must be distinct due to SHA-256 content hashing
    queue = at.session_state["uploaded_resumes_cache"]
    assert len(queue) == 2
    id1 = queue[0]["doc_id"]
    id2 = queue[1]["doc_id"]
    assert id1 != id2
    assert queue[0]["filename"] == "resume.txt"
    assert queue[1]["filename"] == "resume.txt"

    # Screen both candidates
    analyze_btns = [b for b in at.button if "Analyze & Rank" in b.label]
    analyze_btns[0].click().run()
    assert not at.exception

    results = at.session_state["screening_results"]
    assert len(results) == 2
    assert results[0]["doc_id"] == id1 or results[1]["doc_id"] == id1
    assert results[0]["doc_id"] == id2 or results[1]["doc_id"] == id2

    # Remove only candidate 1 (id1) using the UI expander
    at.selectbox(key="sel_remove_single_resume").set_value(id1).run()
    rem_btns = [b for b in at.button if "Remove Selected Document" in b.label]
    rem_btns[0].click().run()

    # Active queue must contain strictly id2
    new_queue = at.session_state["uploaded_resumes_cache"]
    assert len(new_queue) == 1
    assert new_queue[0]["doc_id"] == id2
    assert new_queue[0]["filename"] == "resume.txt"

    # Screening results must contain strictly candidate 2 (id2) at rank 1
    new_results = at.session_state["screening_results"]
    assert len(new_results) == 1
    assert new_results[0]["doc_id"] == id2
    assert new_results[0]["rank"] == 1
    assert new_results[0]["filename"] == "resume.txt"


def test_queue_clearing_resets_all_candidate_and_screening_state():
    """[Widget-Lifecycle] Edge Case 5: Verify that clearing the queue resets selected candidate state,

    analyzed filenames, cached results, uploader tracking, and all associated session state.
    """
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    at.text_area(key="jd_textarea").input(SAMPLE_JD).run()
    at.file_uploader[0].upload("r1.txt", b"Candidate 1 Python").upload("r2.txt", b"Candidate 2 Java").run()

    # Screen candidates
    analyze_btns = [b for b in at.button if "Analyze & Rank" in b.label]
    analyze_btns[0].click().run()

    assert len(at.session_state["screening_results"]) == 2
    assert at.session_state["selected_candidate_id"] is not None
    assert len(at.session_state["analyzed_filenames"]) == 2

    old_uploader_key = f"resume_uploader_{at.session_state.get('uploader_key', 0)}"

    # Click Clear Resume Queue
    clear_btns = [b for b in at.button if "Clear Resume Queue" in b.label]
    assert len(clear_btns) == 1
    clear_btns[0].click().run()

    # Verify complete reset
    assert at.session_state["uploaded_resumes_cache"] == []
    assert at.session_state["screening_results"] == []
    assert at.session_state["selected_candidate_id"] is None
    assert at.session_state["analyzed_filenames"] == []
    assert at.session_state["uploader_known_doc_ids"] in (None, set())
    assert at.session_state["removed_doc_ids"] == set()
    assert old_uploader_key not in at.session_state

    # Verify empty state UI rendering
    content = " ".join(m.value for m in at.markdown)
    assert "No candidates currently screened" in content
    assert "Supported formats:" in content


def test_removed_resumes_stay_removed_across_multipage_navigation():
    """[Widget-Lifecycle] Verify page navigation retains active resumes and does not restore removed ones."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    at.text_area(key="jd_textarea").input(SAMPLE_JD).run()
    at.file_uploader[0].upload("r1.txt", b"R1 Python").upload("r2.txt", b"R2 Java").run()
    assert len(at.session_state["uploaded_resumes_cache"]) == 2

    # Remove r2.txt via uploader drop
    at.file_uploader[0].upload("r1.txt", b"R1 Python").run()
    assert len(at.session_state["uploaded_resumes_cache"]) == 1

    # Navigate to Screening Overview
    at.radio[0].set_value("Screening Overview").run()
    assert not at.exception
    assert len(at.session_state["uploaded_resumes_cache"]) == 1

    # Navigate to Candidate Review
    at.radio[0].set_value("Candidate Review").run()
    assert not at.exception
    assert len(at.session_state["uploaded_resumes_cache"]) == 1

    # Navigate back to Candidates
    at.radio[0].set_value("Candidates").run()
    assert not at.exception
    assert len(at.session_state["uploaded_resumes_cache"]) == 1
    assert at.session_state["uploaded_resumes_cache"][0]["filename"] == "r1.txt"


def test_clear_all_resumes_via_uploader_drop():
    """[Widget-Lifecycle] Verify dropping all files in uploader resets active queue to 0."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    at.file_uploader[0].upload("res1.txt", b"Res 1").upload("res2.txt", b"Res 2").run()
    assert len(at.session_state["uploaded_resumes_cache"]) == 2

    # Clear all from uploader
    at.file_uploader[0].clear().run()
    assert not at.exception

    # Cache must now be empty
    assert len(at.session_state["uploaded_resumes_cache"]) == 0
    content = " ".join(m.value for m in at.markdown)
    assert "candidate document(s) in active queue" not in content
    assert "Supported formats:" in content


def test_reuploading_previously_removed_resume():
    """[Widget-Lifecycle] Verify that a user who removes a resume and then re-uploads it can have it screened."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    r1_bytes = b"Jane Python Dev"
    r2_bytes = b"John Java Dev"

    # Upload 2
    at.file_uploader[0].upload("jane.txt", r1_bytes).upload("john.txt", r2_bytes).run()
    assert len(at.session_state["uploaded_resumes_cache"]) == 2

    # Remove john.txt
    at.file_uploader[0].upload("jane.txt", r1_bytes).run()
    assert len(at.session_state["uploaded_resumes_cache"]) == 1

    # Re-upload john.txt
    at.file_uploader[0].upload("jane.txt", r1_bytes).upload("john.txt", r2_bytes).run()
    assert len(at.session_state["uploaded_resumes_cache"]) == 2
    filenames = [c["filename"] for c in at.session_state["uploaded_resumes_cache"]]
    assert "jane.txt" in filenames
    assert "john.txt" in filenames


# ==============================================================================
# SECTION B: FOCUSED UNIT TESTS ON DOCUMENT IDENTITY & PRUNING LOGIC
# ==============================================================================

def test_compute_document_id_stability_and_uniqueness():
    """[Unit Test] Verify document ID is deterministic for identical content and distinct for different content."""
    b1 = b"Candidate Alice resume content with Python and SQL"
    b2 = b"Candidate Bob resume content with Java and Spring"
    b3 = b"Candidate Alice resume content with Python and SQL"

    id1 = compute_document_id("alice.txt", b1)
    id2 = compute_document_id("bob.txt", b2)
    id3 = compute_document_id("alice.txt", b3)
    id4 = compute_document_id("alice_copy.txt", b1)

    assert id1 == id3, "Identical content and filename must yield identical doc_id"
    assert id1 != id2, "Different content must yield different doc_id"
    assert id1 != id4, "Different filename must yield different doc_id"


def test_prune_screening_results_doc_id_primary_and_legacy_fallback():
    """[Unit Test] Edge Case 4: Verify prune_screening_results uses doc_id as primary identity

    and only uses filename fallback for legacy results lacking a usable doc_id.
    """
    mock_state = {
        "screening_results": [
            {"candidate_id": "CAND_001_dup.pdf", "doc_id": "dup.pdf_AAAA", "filename": "dup.pdf", "rank": 1},
            {"candidate_id": "CAND_002_dup.pdf", "doc_id": "dup.pdf_BBBB", "filename": "dup.pdf", "rank": 2},
            {"candidate_id": "CAND_003_legacy.txt", "doc_id": None, "filename": "legacy.txt", "rank": 3}
        ],
        "selected_candidate_id": "CAND_001_dup.pdf",
        "analyzed_filenames": ["dup.pdf", "dup.pdf", "legacy.txt"]
    }

    # Remove doc_id "dup.pdf_AAAA" while passing filename "dup.pdf"
    prune_screening_results({"dup.pdf_AAAA"}, {"dup.pdf"}, state=mock_state)

    results = mock_state["screening_results"]
    assert len(results) == 2, "Only dup.pdf_AAAA should be removed; dup.pdf_BBBB and legacy.txt must remain"

    # dup.pdf_BBBB must be retained despite having filename "dup.pdf"
    assert results[0]["doc_id"] == "dup.pdf_BBBB"
    assert results[0]["rank"] == 1
    assert results[1]["filename"] == "legacy.txt"
    assert results[1]["rank"] == 2

    # Selected candidate was CAND_001_dup.pdf (removed), so fallback to first remaining
    assert mock_state["selected_candidate_id"] == "CAND_002_dup.pdf"

    # Now remove the legacy document using its filename
    prune_screening_results(set(), {"legacy.txt"}, state=mock_state)
    assert len(mock_state["screening_results"]) == 1
    assert mock_state["screening_results"][0]["doc_id"] == "dup.pdf_BBBB"
    assert mock_state["screening_results"][0]["rank"] == 1


def test_pruning_screened_candidates_reindexes_ranks():
    """[Unit Test] Verify prune_screening_results recalculates ranks #1..N and resets selected_candidate_id."""
    cand1 = {"candidate_id": "CAND_001_a.txt", "doc_id": "a_id", "filename": "a.txt", "rank": 1, "overall_score": 90.0}
    cand2 = {"candidate_id": "CAND_002_b.txt", "doc_id": "b_id", "filename": "b.txt", "rank": 2, "overall_score": 75.0}
    cand3 = {"candidate_id": "CAND_003_c.txt", "doc_id": "c_id", "filename": "c.txt", "rank": 3, "overall_score": 60.0}

    mock_state = {
        "screening_results": [cand1, cand2, cand3],
        "selected_candidate_id": "CAND_002_b.txt",
        "analyzed_filenames": ["a.txt", "b.txt", "c.txt"]
    }

    # Prune cand2
    prune_screening_results({"b_id"}, {"b.txt"}, state=mock_state)

    results = mock_state["screening_results"]
    assert len(results) == 2
    assert results[0]["filename"] == "a.txt"
    assert results[0]["rank"] == 1
    assert results[1]["filename"] == "c.txt"
    assert results[1]["rank"] == 2

    # Selected candidate was b.txt, so it should fallback to first remaining (CAND_001_a.txt)
    assert mock_state["selected_candidate_id"] == "CAND_001_a.txt"
    assert mock_state["analyzed_filenames"] == ["a.txt", "c.txt"]
