"""
End-to-end integration and Streamlit AppTest tests.
Covers:
- Streamlit application loading without exceptions
- End-to-end simulation of resume parsing, scoring, ranking, and CSV generation
"""

import os
from streamlit.testing.v1 import AppTest
from resume_parser import parse_resume
from matcher import rank_resumes
from exporter import generate_candidates_csv
from app import SAMPLE_JOB_DESCRIPTION


def test_streamlit_app_loads_successfully():
    """Verify that app.py initializes and renders title/widgets without runtime errors."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()
    assert not at.exception
    # Ensure markdown or widgets are rendered
    assert len(at.markdown) > 0


def test_load_sample_job_description_button():
    """Verify clicking 'Load Sample Java Job Description' populates the text area with Java Full Stack JD."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Initially empty
    assert at.text_area(key="jd_textarea").value == ""

    # Find and click the load sample button
    load_btns = [b for b in at.button if "Load Sample" in b.label]
    assert len(load_btns) == 1
    load_btns[0].click().run()

    # Value should match SAMPLE_JOB_DESCRIPTION and contain expected keywords
    jd_val = at.text_area(key="jd_textarea").value
    assert jd_val == SAMPLE_JOB_DESCRIPTION
    assert "Java" in jd_val
    assert "Spring Boot" in jd_val
    assert "REST APIs" in jd_val
    assert "MySQL" in jd_val
    assert "Git" in jd_val
    assert "experience" in jd_val.lower()


def test_clear_job_description_button():
    """Verify clicking 'Clear Job Description' empties the text area."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # First load sample
    load_btns = [b for b in at.button if "Load Sample" in b.label]
    load_btns[0].click().run()
    assert at.text_area(key="jd_textarea").value != ""

    # Then click clear
    clear_btns = [b for b in at.button if "Clear Job Description" in b.label]
    assert len(clear_btns) == 1
    clear_btns[0].click().run()

    # Should now be empty
    assert at.text_area(key="jd_textarea").value == ""


def test_end_to_end_screening_workflow():
    """Simulate complete recruiter workflow on all sample resumes."""
    resumes_dir = "sample_resumes"
    filenames = ["resume_01_strong_match.txt", "resume_02_partial_match.docx", "resume_03_unrelated.txt"]
    
    parsed_resumes = []
    for fname in filenames:
        path = os.path.join(resumes_dir, fname)
        assert os.path.exists(path), f"Sample resume {fname} must exist"
        with open(path, "rb") as f:
            parsed = parse_resume(f.read(), fname)
            parsed_resumes.append(parsed)

    # All three must parse successfully
    assert all(p["success"] for p in parsed_resumes)

    # Rank against sample Java job description
    ranked = rank_resumes(SAMPLE_JOB_DESCRIPTION, parsed_resumes)
    assert len(ranked) == 3

    # Rank 1: Strong match
    assert ranked[0]["filename"] == "resume_01_strong_match.txt"
    assert ranked[0]["overall_score"] > 50.0
    assert ranked[0]["skill_match_score"] == 100.0

    # Rank 2: Partial match
    assert ranked[1]["filename"] == "resume_02_partial_match.docx"
    assert 20.0 <= ranked[1]["overall_score"] < ranked[0]["overall_score"]

    # Rank 3: Unrelated match
    assert ranked[2]["filename"] == "resume_03_unrelated.txt"
    assert ranked[2]["overall_score"] < ranked[1]["overall_score"]
    assert ranked[2]["skill_match_score"] == 0.0

    # Generate CSV report
    csv_report = generate_candidates_csv(ranked)
    assert "Alex Morgan" in csv_report
    assert "Jordan Lee" in csv_report
    assert "Taylor Smith" in csv_report
    assert "resume_01_strong_match.txt" in csv_report


def test_leaderboard_rendering_without_pandas():
    """Verify candidate leaderboard renders without invoking pandas or raising exceptions."""
    resumes_dir = "sample_resumes"
    filenames = ["resume_01_strong_match.txt", "resume_02_partial_match.docx", "resume_03_unrelated.txt"]

    parsed_resumes = []
    for fname in filenames:
        path = os.path.join(resumes_dir, fname)
        with open(path, "rb") as f:
            parsed = parse_resume(f.read(), fname)
            parsed_resumes.append(parsed)

    ranked = rank_resumes(SAMPLE_JOB_DESCRIPTION, parsed_resumes)

    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()
    # Inject ranked results into session_state to test results rendering
    at.session_state["screening_results"] = ranked
    at.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at.run()

    # Verify no exceptions (such as pandas DLL or table import errors) were raised
    assert not at.exception

    # Verify leaderboard HTML table is present in rendered markdown
    table_markdowns = [m for m in at.markdown if "leaderboard-table" in m.value and "<table" in m.value]
    assert len(table_markdowns) == 1

    table_content = table_markdowns[0].value
    # Verify headers
    assert "<th>Rank</th>" in table_content
    assert "<th>Candidate Name</th>" in table_content
    assert "<th>Original Filename</th>" in table_content
    assert "<th>Overall Score</th>" in table_content
    assert "<th>Text Similarity</th>" in table_content
    assert "<th>Skill Match</th>" in table_content
    assert "<th>Matched Skills</th>" in table_content
    assert "<th>Review Status</th>" in table_content

    # Verify candidate rows are present and properly ranked
    assert "#1" in table_content
    assert "Alex Morgan" in table_content
    assert "resume_01_strong_match.txt" in table_content
    assert "Jordan Lee" in table_content
    assert "resume_02_partial_match.docx" in table_content
    assert "Taylor Smith" in table_content
    assert "resume_03_unrelated.txt" in table_content


def test_candidate_field_mapping_and_warning_handling():
    """Verify that candidate details map correctly and sparse text triggers a warning."""
    resumes_dir = "sample_resumes"
    all_files = [
        "resume_01_strong_match.txt",
        "resume_02_partial_match.docx",
        "resume_03_unrelated.txt",
        "resume_04_python_dev.pdf"
    ]

    parsed_resumes = []
    for fname in all_files:
        path = os.path.join(resumes_dir, fname)
        with open(path, "rb") as f:
            parsed = parse_resume(f.read(), fname)
            parsed_resumes.append(parsed)

    # Verify field integrity in parsed resumes
    r1 = next(r for r in parsed_resumes if r["filename"] == "resume_01_strong_match.txt")
    assert r1["name"] == "Alex Morgan"
    assert r1["emails"] == ["alex.morgan@example.com"]
    assert "+1 555-019-2834" in r1["phones"]
    assert r1["warning"] is None

    r3 = next(r for r in parsed_resumes if r["filename"] == "resume_03_unrelated.txt")
    assert r3["name"] == "Taylor Smith"
    assert r3["emails"] == ["taylor.smith@example.com"]
    # Phone must have proper formatting and not distorted
    assert "(555) 789-1023" in r3["phones"]

    # Realistic PDF extraction for David Kim (resume_04_python_dev.pdf)
    r4 = next(r for r in parsed_resumes if r["filename"] == "resume_04_python_dev.pdf")
    assert r4["warning"] is None
    assert r4["name"] == "David Kim"
    assert "david.kim@example.com" in r4["emails"]

    # Test that sparse text content is properly flagged with a warning
    sparse_parsed = parse_resume(b"Jane Doe\nEmail: jane@example.com", "sparse_sample.txt")
    assert sparse_parsed["warning"] is not None
    assert "limited extractable text" in sparse_parsed["warning"]

    # Rank and verify candidate dictionary alignment
    ranked = rank_resumes(SAMPLE_JOB_DESCRIPTION, parsed_resumes)
    assert len(ranked) == 4

    # Verify ranks are ordered descending by score
    scores = [c["overall_score"] for c in ranked]
    assert scores == sorted(scores, reverse=True)

    # Verify warning forwarding into ranked candidate record for a sparse candidate
    ranked_with_sparse = rank_resumes(SAMPLE_JOB_DESCRIPTION, [sparse_parsed])
    assert ranked_with_sparse[0]["warning"] is not None


def test_multipage_ats_navigation_and_rendering():
    """Verify that all three ATS pages navigate and render correctly with loaded screening results."""
    resumes_dir = "sample_resumes"
    filenames = ["resume_01_strong_match.txt", "resume_02_partial_match.docx", "resume_03_unrelated.txt"]

    parsed_resumes = []
    for fname in filenames:
        path = os.path.join(resumes_dir, fname)
        with open(path, "rb") as f:
            parsed = parse_resume(f.read(), fname)
            parsed_resumes.append(parsed)

    ranked = rank_resumes(SAMPLE_JOB_DESCRIPTION, parsed_resumes)
    app_path = os.path.abspath("app.py")

    # 1. Test Page: Candidates Overview
    at_cand = AppTest.from_file(app_path, default_timeout=15)
    at_cand.run()
    at_cand.session_state["screening_results"] = ranked
    at_cand.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at_cand.run()
    assert not at_cand.exception
    content_cand = " ".join(m.value for m in at_cand.markdown)
    assert "Candidates" in content_cand
    assert "Job Description Setup" in content_cand

    # 2. Test Page: Screening Overview & Analytics
    at_overview = AppTest.from_file(app_path, default_timeout=15)
    at_overview.run()
    at_overview.session_state["screening_results"] = ranked
    at_overview.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at_overview.radio[0].set_value("Screening Overview").run()
    assert not at_overview.exception
    content_overview = " ".join(m.value for m in at_overview.markdown)
    assert "Screening Overview" in content_overview
    assert "Required Competency Coverage" in content_overview
    assert "Candidate Match Comparison" in content_overview

    # 3. Test Page: Candidate Review Workspace
    at_review = AppTest.from_file(app_path, default_timeout=15)
    at_review.run()
    at_review.session_state["screening_results"] = ranked
    at_review.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at_review.session_state["selected_candidate_id"] = ranked[0]["candidate_id"]
    at_review.radio[0].set_value("Candidate Review").run()
    assert not at_review.exception
    content_review = " ".join(m.value for m in at_review.markdown)
    assert "Candidate Review" in content_review
    assert "Candidate Queue" in content_review
    assert "Alex Morgan" in content_review
    assert "Composite Match" in content_review


def test_dynamic_job_title_and_screening_state_synchronization():
    """Verify dynamic title extraction, state synchronization across pages, and clearing behavior."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()
    assert not at.exception

    # 1. Load sample JD: Header must display Job: Java Full Stack Developer and Processing: Local
    load_btns = [b for b in at.button if "Load Sample" in b.label]
    load_btns[0].click().run()
    markdown_content = " ".join(m.value for m in at.markdown)
    assert "Job: Java Full Stack Developer" in markdown_content
    assert "Processing: Local" in markdown_content
    assert "Local Engine" not in markdown_content

    # 2. Clear JD: Header must switch to Job: Not Specified across pages and disable Analyze
    clear_btns = [b for b in at.button if "Clear Job Description" in b.label]
    clear_btns[0].click().run()
    markdown_cleared = " ".join(m.value for m in at.markdown)
    assert "Job: Not Specified" in markdown_cleared
    # Analyze button should be disabled
    analyze_btns = [b for b in at.button if "Analyze & Rank" in b.label]
    assert len(analyze_btns) == 1
    assert analyze_btns[0].disabled is True

    # 3. Enter a custom role (Python Developer)
    at.text_area(key="jd_textarea").input("Role: Python Developer\nRequired: Python, Django, PostgreSQL, Docker").run()
    markdown_python = " ".join(m.value for m in at.markdown)
    assert "Job: Python Developer" in markdown_python

    # 4. Analyze button should now be enabled
    analyze_btns = [b for b in at.button if "Analyze & Rank" in b.label]
    assert analyze_btns[0].disabled is False


def test_scenario_1_load_sample_jd_does_not_populate_candidates():
    """Scenario 1: Clicking Load Sample JD only populates text area, screening_results remains empty."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Initially empty
    assert len(at.session_state["screening_results"]) == 0

    # Click Load Sample JD
    load_btns = [b for b in at.button if "Load Sample" in b.label]
    load_btns[0].click().run()

    # JD populated, but screening_results MUST remain empty
    assert at.text_area(key="jd_textarea").value == SAMPLE_JOB_DESCRIPTION
    assert len(at.session_state["screening_results"]) == 0
    markdown_content = " ".join(m.value for m in at.markdown)
    assert "No candidates currently screened" in markdown_content
    assert "Alex Morgan" not in markdown_content


def test_scenario_2_and_4_upload_single_user_resume_screens_only_uploaded():
    """Scenario 2 & 4: Uploading a unique resume screens ONLY that resume, never sample candidates."""
    # Synthetic resume for Jane Doe
    user_resume_content = (
        "Jane Doe\nEmail: jane.doe@example.com\nPhone: (555) 234-5678\n\n"
        "Professional Summary:\nSenior Java Developer with 6 years experience in Java, Spring Boot, REST APIs, and MySQL.\n"
        "Technical Skills:\nJava, Spring Boot, REST APIs, MySQL, Git, Docker\n"
        "Education:\nBachelor of Science in Computer Science, State University\n"
        "Experience:\nLead Java Engineer at Tech Corp - Built Spring Boot microservices and REST APIs."
    )
    parsed = parse_resume(user_resume_content.encode("utf-8"), "jane_doe_resume.txt")
    assert parsed["success"] is True
    assert parsed["name"] == "Jane Doe"

    ranked = rank_resumes(SAMPLE_JOB_DESCRIPTION, [parsed])
    assert len(ranked) == 1
    assert ranked[0]["name"] == "Jane Doe"
    assert ranked[0]["filename"] == "jane_doe_resume.txt"

    # Verify rendering in app
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Simulate Load Sample JD then screening Jane Doe
    load_btns = [b for b in at.button if "Load Sample" in b.label]
    load_btns[0].click().run()

    at.session_state["screening_results"] = ranked
    at.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["selected_candidate_id"] = ranked[0]["candidate_id"]
    at.run()

    content = " ".join(m.value for m in at.markdown)
    assert "Jane Doe" in content
    assert "jane_doe_resume.txt" in content
    # Ensure none of the sample candidates are present
    assert "Alex Morgan" not in content
    assert "Jordan Lee" not in content
    assert "Taylor Smith" not in content
    assert "David Kim" not in content


def test_scenario_3_upload_multiple_user_resumes():
    """Scenario 3: Uploading two unique resumes ranks exactly those two candidates."""
    res1 = (
        "Alice Smith\nEmail: alice@example.com\n"
        "Java, Spring Boot, MySQL, REST APIs, Git. 5 years experience."
    )
    res2 = (
        "Bob Johnson\nEmail: bob@example.com\n"
        "Frontend developer. React, CSS, HTML, JavaScript."
    )
    parsed1 = parse_resume(res1.encode("utf-8"), "alice_smith.txt")
    parsed2 = parse_resume(res2.encode("utf-8"), "bob_johnson.txt")

    ranked = rank_resumes(SAMPLE_JOB_DESCRIPTION, [parsed1, parsed2])
    assert len(ranked) == 2
    assert ranked[0]["name"] == "Alice Smith"
    assert ranked[1]["name"] == "Bob Johnson"
    assert ranked[0]["overall_score"] > ranked[1]["overall_score"]

    csv_out = generate_candidates_csv(ranked)
    assert "Alice Smith" in csv_out
    assert "Bob Johnson" in csv_out
    assert "Alex Morgan" not in csv_out


def test_scenario_5_rescreen_with_different_resume_replaces_old():
    """Scenario 5: Re-screening with a different resume completely replaces prior results."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # First screening: Candidate 1
    p1 = parse_resume(b"First Candidate\nEmail: first@test.com\nSkills: Java", "first.txt")
    ranked1 = rank_resumes(SAMPLE_JOB_DESCRIPTION, [p1])
    at.session_state["screening_results"] = ranked1
    at.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at.run()
    assert "First Candidate" in " ".join(m.value for m in at.markdown)

    # Second screening: Candidate 2 replaces Candidate 1
    p2 = parse_resume(b"Second Candidate\nEmail: second@test.com\nSkills: Python", "second.txt")
    ranked2 = rank_resumes(SAMPLE_JOB_DESCRIPTION, [p2])
    at.session_state["screening_results"] = ranked2
    at.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at.run()
    content2 = " ".join(m.value for m in at.markdown)
    assert "Second Candidate" in content2
    assert "First Candidate" not in content2


def test_scenario_6_malformed_file_handling():
    """Scenario 6: Malformed / unparseable file is flagged without falling back to sample resumes."""
    malformed_pdf = b"%PDF-1.4 completely corrupted binary content that cannot be parsed"
    parsed_bad = parse_resume(malformed_pdf, "corrupt_resume.pdf")
    assert parsed_bad["success"] is False
    assert parsed_bad["error"] is not None

    ranked = rank_resumes(SAMPLE_JOB_DESCRIPTION, [parsed_bad])
    assert len(ranked) == 1
    assert ranked[0]["filename"] == "corrupt_resume.pdf"
    assert ranked[0]["success"] is False
    assert "Extraction failed" in ranked[0]["score_explanation"]

    # In app review, extraction failure is clearly reported
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()
    at.session_state["screening_results"] = ranked
    at.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["selected_candidate_id"] = ranked[0]["candidate_id"]
    at.run()
    content = " ".join(m.value for m in at.markdown)
    assert "corrupt_resume.pdf" in content
    assert "Extraction failed" in content
    assert "Alex Morgan" not in content


def test_scenario_7_analyze_without_uploaded_resumes():
    """Scenario 7: Clicking Analyze with a valid JD but no resumes displays required upload error."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Load JD so JD is ready
    load_btns = [b for b in at.button if "Load Sample" in b.label]
    load_btns[0].click().run()

    # Analyze button should be enabled
    analyze_btns = [b for b in at.button if "Analyze & Rank" in b.label]
    assert analyze_btns[0].disabled is False

    # Click Analyze without any uploaded resumes
    analyze_btns[0].click().run()

    # Should show error message and screening_results must remain empty
    assert len(at.session_state["screening_results"]) == 0
    assert len(at.error) > 0
    error_texts = " ".join(e.value for e in at.error)
    assert "Please upload at least one candidate resume document" in error_texts


def test_scenario_8_clear_jd_clears_all_screening_state():
    """Scenario 8: Clicking Clear Job Description resets JD and all screening results."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Populate JD and fake screening results
    load_btns = [b for b in at.button if "Load Sample" in b.label]
    load_btns[0].click().run()
    p = parse_resume(b"Jane Doe\nEmail: jane@test.com\nJava", "jane.txt")
    at.session_state["screening_results"] = rank_resumes(SAMPLE_JOB_DESCRIPTION, [p])
    at.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["selected_candidate_id"] = at.session_state["screening_results"][0]["candidate_id"]
    at.run()

    assert len(at.session_state["screening_results"]) == 1

    # Click Clear Job Description
    clear_btns = [b for b in at.button if "Clear Job Description" in b.label]
    clear_btns[0].click().run()

    assert at.text_area(key="jd_textarea").value == ""
    assert at.session_state["screening_results"] == []
    assert at.session_state["analyzed_jd"] == ""
    assert at.session_state["selected_candidate_id"] is None


def test_scenario_9_explicit_demo_sample_resumes_button():
    """Scenario 9: Clicking 'Load & Screen Sample Resumes (Demo)' explicitly evaluates sample resumes with demo warning."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Load JD first
    load_btns = [b for b in at.button if "Load Sample" in b.label]
    load_btns[0].click().run()

    # Click explicit demo sample button
    demo_btns = [b for b in at.button if "Sample Resumes (Demo)" in b.label]
    assert len(demo_btns) == 1
    demo_btns[0].click().run()

    assert not at.exception
    # Should populate candidates with demo tags
    assert len(at.session_state["screening_results"]) == 4
    for cand in at.session_state["screening_results"]:
        assert cand.get("warning") == "Demo Sample Candidate"

    content = " ".join(m.value for m in at.markdown)
    assert "Alex Morgan" in content


def test_scenario_10_stale_jd_warning_displayed():
    """Scenario 10: Changing the job description in editor triggers stale results warning."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Load JD and pretend we screened a candidate
    load_btns = [b for b in at.button if "Load Sample" in b.label]
    load_btns[0].click().run()
    p = parse_resume(b"Jane Doe\nEmail: jane@test.com\nJava", "jane.txt")
    at.session_state["screening_results"] = rank_resumes(SAMPLE_JOB_DESCRIPTION, [p])
    at.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at.run()

    # Initially not stale
    assert len(at.warning) == 0

    # Modify the text area
    at.text_area(key="jd_textarea").input("Role: Python Engineer\nResponsibilities: Develop Django web apps.").run()

    # Stale warning should now be rendered
    assert len(at.warning) > 0
    warning_text = " ".join(w.value for w in at.warning)
    assert "modified since the last screening run" in warning_text


def test_navigation_preserves_custom_job_description():
    """Verify that entering a custom JD persists across multi-page navigation."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    custom_jd = "Role: Machine Learning Engineer\nRequired: Python, PyTorch, TensorFlow, Docker, MLOps."
    at.text_area(key="jd_textarea").input(custom_jd).run()
    assert at.session_state["persistent_jd_text"] == custom_jd

    # Navigate to Screening Overview
    at.radio[0].set_value("Screening Overview").run()
    assert not at.exception
    assert "Job: Machine Learning Engineer" in " ".join(m.value for m in at.markdown)

    # Navigate to Candidate Review
    at.radio[0].set_value("Candidate Review").run()
    assert not at.exception
    assert "Job: Machine Learning Engineer" in " ".join(m.value for m in at.markdown)

    # Navigate back to Candidates
    at.radio[0].set_value("Candidates").run()
    assert not at.exception
    assert at.text_area(key="jd_textarea").value == custom_jd
    assert at.session_state["persistent_jd_text"] == custom_jd
    assert "Job: Machine Learning Engineer" in " ".join(m.value for m in at.markdown)


def test_navigation_preserves_upload_queue_metadata():
    """Verify that uploaded file metadata persists across multi-page navigation."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Simulate queued files in session state
    at.session_state["persistent_jd_text"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["uploaded_resumes_cache"] = [
        {"filename": "resume_alpha.pdf", "bytes": b"%PDF-1.4...", "size": 1234},
        {"filename": "resume_beta.docx", "bytes": b"PK...", "size": 5678}
    ]
    at.run()

    content_cand1 = " ".join(m.value for m in at.markdown)
    assert "candidate document(s) in active queue" in content_cand1
    assert "2" in content_cand1

    # Navigate to Screening Overview
    at.radio[0].set_value("Screening Overview").run()
    assert not at.exception

    # Navigate back to Candidates
    at.radio[0].set_value("Candidates").run()
    assert not at.exception

    # Queue must still be present
    content_cand2 = " ".join(m.value for m in at.markdown)
    assert "candidate document(s) in active queue" in content_cand2
    assert "2" in content_cand2
    assert len(at.session_state["uploaded_resumes_cache"]) == 2


def test_clear_queue_button_removes_files_without_affecting_jd():
    """Verify clearing the resume queue resets queued files while leaving the JD intact."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    at.session_state["persistent_jd_text"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["uploaded_resumes_cache"] = [
        {"filename": "test.txt", "bytes": b"test content", "size": 12}
    ]
    at.run()

    # Clear Resume Queue button
    clear_q_btns = [b for b in at.button if "Clear Resume Queue" in b.label]
    assert len(clear_q_btns) == 1
    clear_q_btns[0].click().run()

    # Queue is empty, JD remains intact
    assert len(at.session_state["uploaded_resumes_cache"]) == 0
    assert at.text_area(key="jd_textarea").value == SAMPLE_JOB_DESCRIPTION


def test_stale_warning_when_queue_changes():
    """Verify that altering the queued files after screening triggers a queue stale warning."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Screened candidate
    p = parse_resume(b"Jane Doe\nEmail: jane@test.com\nJava", "resume_original.txt")
    ranked = rank_resumes(SAMPLE_JOB_DESCRIPTION, [p])
    at.session_state["screening_results"] = ranked
    at.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["persistent_jd_text"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["analyzed_filenames"] = ["resume_original.txt"]
    at.session_state["uploaded_resumes_cache"] = [
        {"filename": "resume_original.txt", "bytes": b"content", "size": 10}
    ]
    at.run()

    # No warning initially
    assert len(at.warning) == 0

    # User modifies queue with a new document
    at.session_state["uploaded_resumes_cache"] = [
        {"filename": "resume_updated.txt", "bytes": b"new content", "size": 20}
    ]
    at.run()

    # Queue staleness warning should appear
    assert len(at.warning) > 0
    warning_text = " ".join(w.value for w in at.warning)
    assert "screening queue have changed" in warning_text


def test_data_scientist_8_candidates_workflow():
    """Verify screening 8 Data Scientist candidates and persistence across navigation."""
    ds_dir = os.path.join("sample_resumes", "data_scientist_test")
    assert os.path.exists(ds_dir)

    ds_files = [
        "candidate_01_lead_ds.txt",
        "candidate_02_ml_eng.txt",
        "candidate_03_nlp_scientist.txt",
        "candidate_04_data_analyst.txt",
        "candidate_05_python_dev.txt",
        "candidate_06_bi_analyst.txt",
        "candidate_07_junior_ds.txt",
        "candidate_08_sales.txt"
    ]

    parsed_all = []
    cached_queue = []
    for fname in ds_files:
        fpath = os.path.join(ds_dir, fname)
        with open(fpath, "rb") as f:
            b = f.read()
            parsed_all.append(parse_resume(b, fname))
            cached_queue.append({"filename": fname, "bytes": b, "size": len(b)})

    ds_jd = (
        "Role: Data Scientist\n"
        "Requirements: Python, Machine Learning, Deep Learning, SQL, Pandas, NumPy, Scikit-Learn, TensorFlow, Statistics, NLP."
    )

    ranked = rank_resumes(ds_jd, parsed_all)
    assert len(ranked) == 8
    # Alice Walker or Brian Chen should outrank Henry Adams (Sales)
    assert ranked[0]["name"] in ["Alice Walker", "Brian Chen", "Clara Evans"]
    assert ranked[-1]["name"] == "Henry Adams"

    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    at.session_state["persistent_jd_text"] = ds_jd
    at.session_state["uploaded_resumes_cache"] = cached_queue
    at.session_state["analyzed_filenames"] = ds_files
    at.session_state["screening_results"] = ranked
    at.session_state["analyzed_jd"] = ds_jd
    at.session_state["selected_candidate_id"] = ranked[0]["candidate_id"]
    at.run()

    content = " ".join(m.value for m in at.markdown)
    assert "candidate document(s) in active queue" in content
    assert "8" in content
    assert "Alice Walker" in content
    assert "Henry Adams" in content

    # Navigate to Screening Overview
    at.radio[0].set_value("Screening Overview").run()
    assert not at.exception
    assert "Job: Data Scientist" in " ".join(m.value for m in at.markdown)

    # Navigate to Candidate Review
    at.radio[0].set_value("Candidate Review").run()
    assert not at.exception
    assert "Alice Walker" in " ".join(m.value for m in at.markdown)

    # Navigate back to Candidates
    at.radio[0].set_value("Candidates").run()
    assert not at.exception
    assert at.text_area(key="jd_textarea").value == ds_jd
    content_cand_back = " ".join(m.value for m in at.markdown)
    assert "candidate document(s) in active queue" in content_cand_back
    assert "8" in content_cand_back


def test_uploading_three_files_displays_all_three_filenames_and_sizes():
    """Verify that uploading 3 files displays all three filenames and file sizes immediately."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    files = [
        {"filename": "resume_01_strong_match.txt", "bytes": b"Alex Morgan resume text...", "size": 1566},
        {"filename": "resume_02_partial_match.docx", "bytes": b"Jordan Lee resume text...", "size": 37115},
        {"filename": "resume_03_unrelated.txt", "bytes": b"Taylor Smith resume text...", "size": 1310}
    ]
    at.session_state["persistent_jd_text"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["uploaded_resumes_cache"] = files
    at.run()

    content = " ".join(m.value for m in at.markdown)
    assert "candidate document(s) in active queue" in content
    assert "3" in content
    # All 3 filenames must be displayed
    assert "resume_01_strong_match.txt" in content
    assert "resume_02_partial_match.docx" in content
    assert "resume_03_unrelated.txt" in content
    # Formatted sizes must be visible
    assert "1.5 KB" in content
    assert "36.2 KB" in content
    assert "1.3 KB" in content


def test_navigating_retains_all_three_files_in_visible_queue():
    """Verify navigating Candidates -> Overview -> Review -> Candidates retains all 3 files."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    files = [
        {"filename": "alpha.txt", "bytes": b"Candidate Alpha", "size": 100},
        {"filename": "beta.pdf", "bytes": b"%PDF-1.4...", "size": 2048},
        {"filename": "gamma.docx", "bytes": b"PK...", "size": 4096}
    ]
    at.session_state["persistent_jd_text"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["uploaded_resumes_cache"] = files
    at.run()

    # 1. Overview
    at.radio[0].set_value("Screening Overview").run()
    assert not at.exception

    # 2. Review
    at.radio[0].set_value("Candidate Review").run()
    assert not at.exception

    # 3. Candidates
    at.radio[0].set_value("Candidates").run()
    assert not at.exception

    content = " ".join(m.value for m in at.markdown)
    assert "candidate document(s) in active queue" in content
    assert "3" in content
    assert "alpha.txt" in content
    assert "beta.pdf" in content
    assert "gamma.docx" in content
    assert len(at.session_state["uploaded_resumes_cache"]) == 3


def test_cached_file_bytes_remain_usable_by_resume_parser():
    """Verify cached file bytes in session state remain usable by parse_resume()."""
    res1_path = os.path.join("sample_resumes", "resume_01_strong_match.txt")
    with open(res1_path, "rb") as f:
        b1 = f.read()

    res2_path = os.path.join("sample_resumes", "resume_02_partial_match.docx")
    with open(res2_path, "rb") as f:
        b2 = f.read()

    cache = [
        {"filename": "resume_01_strong_match.txt", "bytes": b1, "size": len(b1)},
        {"filename": "resume_02_partial_match.docx", "bytes": b2, "size": len(b2)}
    ]

    for item in cache:
        parsed = parse_resume(item["bytes"], item["filename"])
        assert parsed["success"] is True
        assert parsed["name"] is not None
        assert len(parsed["raw_text"]) > 0


def test_uploading_additional_file_updates_queue_without_duplicates():
    """Verify adding a new file appends to cache without duplicating existing files."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    at.session_state["uploaded_resumes_cache"] = [
        {"filename": "doc1.txt", "bytes": b"doc1", "size": 10},
        {"filename": "doc2.txt", "bytes": b"doc2", "size": 20}
    ]

    # Emulate ingestion logic
    existing_filenames = {item["filename"] for item in at.session_state["uploaded_resumes_cache"]}
    new_incoming = [
        {"name": "doc2.txt", "bytes": b"doc2", "size": 20},  # duplicate
        {"name": "doc3.txt", "bytes": b"doc3", "size": 30}   # new
    ]
    for inc in new_incoming:
        if inc["name"] not in existing_filenames:
            at.session_state["uploaded_resumes_cache"].append({
                "filename": inc["name"],
                "bytes": inc["bytes"],
                "size": inc["size"]
            })
            existing_filenames.add(inc["name"])

    assert len(at.session_state["uploaded_resumes_cache"]) == 3
    filenames = [item["filename"] for item in at.session_state["uploaded_resumes_cache"]]
    assert filenames == ["doc1.txt", "doc2.txt", "doc3.txt"]


def test_changing_pages_does_not_clear_queue_or_rescreen():
    """Verify page navigation preserves screening results and does not rescreen."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    p = parse_resume(b"Jane Doe\nEmail: jane@test.com\nJava", "jane.txt")
    ranked = rank_resumes(SAMPLE_JOB_DESCRIPTION, [p])
    initial_score = ranked[0]["overall_score"]

    at.session_state["persistent_jd_text"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["screening_results"] = ranked
    at.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["uploaded_resumes_cache"] = [
        {"filename": "jane.txt", "bytes": b"Jane Doe\nEmail: jane@test.com\nJava", "size": 35}
    ]
    at.run()

    # Navigate to Overview then back
    at.radio[0].set_value("Screening Overview").run()
    assert not at.exception
    at.radio[0].set_value("Candidates").run()
    assert not at.exception

    # Results are unchanged
    assert len(at.session_state["screening_results"]) == 1
    assert at.session_state["screening_results"][0]["overall_score"] == initial_score
    assert len(at.session_state["uploaded_resumes_cache"]) == 1


def test_screening_overview_displays_all_12_candidates():
    """Verify that when 12 candidates are evaluated, all 12 appear in the comparison table."""
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()

    # Generate 12 distinct parsed resumes with varying skills and scores
    parsed_12 = []
    skills_pool = [
        ["Java", "Spring Boot", "MySQL", "Docker", "REST API"],
        ["Java", "Microservices", "PostgreSQL", "Git"],
        ["Java", "Spring Boot", "Docker"],
        ["Python", "Django", "PostgreSQL"],
        ["Java", "Spring Boot"],
        ["JavaScript", "React", "Node.js"],
        ["Java", "MySQL"],
        ["Docker", "Kubernetes", "AWS"],
        ["Git", "Agile", "CI/CD"],
        ["MySQL", "PostgreSQL"],
        ["HTML", "CSS", "JavaScript"],
        ["Project Management", "Agile", "Scrum"]
    ]

    for i in range(1, 13):
        fname = f"candidate_{i:02d}.txt"
        skills_text = " ".join(skills_pool[i - 1])
        raw = f"Candidate {i}\nEmail: cand{i}@example.com\nSkills: {skills_text}\nExperience: Software engineer.\n"
        p = parse_resume(raw.encode("utf-8"), fname)
        parsed_12.append(p)

    assert len(parsed_12) == 12

    # Rank the 12 candidates against sample JD
    ranked_12 = rank_resumes(SAMPLE_JOB_DESCRIPTION, parsed_12)
    assert len(ranked_12) == 12

    # Verify ranks are continuous #1 through #12
    for idx, c in enumerate(ranked_12, start=1):
        assert c["rank"] == idx

    # Seed state and navigate to Screening Overview
    at.session_state["persistent_jd_text"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["screening_results"] = ranked_12
    at.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
    at.session_state["analyzed_filenames"] = [c["filename"] for c in ranked_12]
    at.session_state["uploaded_resumes_cache"] = [
        {"filename": c["filename"], "bytes": b"mock", "size": 100} for c in ranked_12
    ]
    at.radio[0].set_value("Screening Overview").run()
    assert not at.exception

    # Locate markdown block rendering Candidate Match Comparison table
    overview_markdowns = [m.value for m in at.markdown]
    comparison_table_md = next(
        (m for m in overview_markdowns if '<table class="data-table">' in m),
        None
    )
    assert comparison_table_md is not None, "Candidate Match Comparison table not found in rendered markdown"

    # Verify all 12 ranks (#1 to #12) and all 12 filenames appear in the table
    for i in range(1, 13):
        expected_rank_str = f"#{i}</td>"
        expected_file_str = f"candidate_{i:02d}.txt"
        assert expected_rank_str in comparison_table_md, f"Expected rank #{i} not found in comparison table HTML"
        assert expected_file_str in comparison_table_md, f"Expected file {expected_file_str} not found in comparison table HTML"





