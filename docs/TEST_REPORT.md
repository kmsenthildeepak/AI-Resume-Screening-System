# Test Execution Audit Report: AI Resume Screening System

**Test Framework:** `pytest 9.1.1`  
**Execution Environment:** Windows (PowerShell), Python 3.11.9, Pure-Python TF-IDF, PyPDF 6.20.0, python-docx 1.2.0, ReportLab 5.0.1  
**Test Date:** 2026-10-12  
**Test Execution Result:** **48 Passed, 0 Failed, 0 Skipped (100% Pass Rate)**  

---

## 1. Summary of Execution

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- E:\AI_Resume_Screening_System\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: E:\AI_Resume_Screening_System
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 48 items

tests/test_integration.py::test_streamlit_app_loads_successfully PASSED  [  2%]
tests/test_integration.py::test_load_sample_job_description_button PASSED [  4%]
tests/test_integration.py::test_clear_job_description_button PASSED      [  6%]
tests/test_integration.py::test_end_to_end_screening_workflow PASSED     [  8%]
tests/test_integration.py::test_leaderboard_rendering_without_pandas PASSED [ 10%]
tests/test_integration.py::test_candidate_field_mapping_and_warning_handling PASSED [ 12%]
tests/test_integration.py::test_multipage_ats_navigation_and_rendering PASSED [ 14%]
tests/test_integration.py::test_dynamic_job_title_and_screening_state_synchronization PASSED [ 16%]
tests/test_matcher.py::test_cosine_similarity_identical_and_zero PASSED  [ 18%]
tests/test_matcher.py::test_compute_tfidf_similarities PASSED            [ 19%]
tests/test_matcher.py::test_calculate_skill_match_score_with_preferred PASSED [ 21%]
tests/test_matcher.py::test_strong_match_outranks_unrelated_resume PASSED [ 23%]
tests/test_matcher.py::test_scores_strictly_bounded_between_0_and_100 PASSED [ 25%]
tests/test_matcher.py::test_duplicate_filenames_distinguishable PASSED   [ 27%]
tests/test_matcher.py::test_deterministic_ranking PASSED                 [ 29%]
tests/test_requirement_extractor.py::test_extract_skills_standard PASSED [ 31%]
tests/test_requirement_extractor.py::test_extract_skills_case_insensitive PASSED [ 34%]
tests/test_requirement_extractor.py::test_extract_skills_aliases PASSED  [ 36%]
tests/test_requirement_extractor.py::test_word_boundary_avoids_false_positives PASSED [ 38%]
tests/test_requirement_extractor.py::test_c_plus_plus_and_c_sharp_boundary PASSED [ 40%]
tests/test_requirement_extractor.py::test_extract_skills_empty PASSED    [ 42%]
tests/test_requirement_extractor.py::test_extract_skills_no_known_skills PASSED [ 44%]
tests/test_requirement_extractor.py::test_extract_job_sections_preferred_and_required PASSED [ 46%]
tests/test_requirement_extractor.py::test_extract_job_requirements_full PASSED [ 48%]
tests/test_requirement_extractor.py::test_extract_job_title_empty_and_whitespace PASSED [ 51%]
tests/test_requirement_extractor.py::test_extract_job_title_explicit_headers PASSED [ 53%]
tests/test_requirement_extractor.py::test_extract_job_title_recognized_roles PASSED [ 55%]
tests/test_requirement_extractor.py::test_extract_job_title_fallback_custom PASSED [ 57%]
tests/test_resume_parser.py::test_txt_valid_extraction PASSED            [ 59%]
tests/test_resume_parser.py::test_txt_unicode_extraction PASSED          [ 61%]
tests/test_resume_parser.py::test_txt_empty_raises_value_error PASSED    [ 63%]
tests/test_resume_parser.py::test_docx_valid_extraction PASSED           [ 65%]
tests/test_resume_parser.py::test_docx_empty_raises_value_error PASSED   [ 68%]
tests/test_resume_parser.py::test_docx_malformed_raises_value_error PASSED [ 70%]
tests/test_resume_parser.py::test_pdf_valid_extraction PASSED            [ 72%]
tests/test_resume_parser.py::test_pdf_malformed_raises_value_error PASSED [ 74%]
tests/test_resume_parser.py::test_unsupported_extension PASSED           [ 76%]
tests/test_resume_parser.py::test_file_size_exceeded PASSED              [ 78%]
tests/test_resume_parser.py::test_email_extraction PASSED                [ 80%]
tests/test_resume_parser.py::test_phone_extraction PASSED                [ 82%]
tests/test_resume_parser.py::test_candidate_name_heuristic PASSED        [ 85%]
tests/test_resume_parser.py::test_parse_resume_end_to_end_success PASSED [ 87%]
tests/test_resume_parser.py::test_parse_resume_end_to_end_failure PASSED [ 89%]
tests/test_resume_parser.py::test_parse_sample_pdf_resume_04 PASSED      [ 91%]
tests/test_validation.py::test_sanitize_csv_cell_formula_injection PASSED [ 93%]
tests/test_validation.py::test_sanitize_csv_cell_normal_values PASSED    [ 95%]
tests/test_validation.py::test_generate_candidates_csv_structure PASSED  [ 97%]
tests/test_validation.py::test_generate_candidates_csv_unicode PASSED    [100%]

============================= 48 passed in 1.93s ==============================
```

---

## 2. Granular Test Suite Coverage

### A. Document Parser (`tests/test_resume_parser.py` - 16 Tests)
- **Valid Formats:** Verified extraction from TXT, DOCX paragraphs & tables, and text-based PDFs.
- **Realistic Synthetic PDF:** Tested comprehensive extraction of `sample_resumes/resume_04_python_dev.pdf` (David Kim, 304 words, zero xref warnings, Python/Django/PostgreSQL skills, no sparse text warnings).
- **Defensive Error Handling:** Tested empty TXT files, empty DOCX files, corrupted DOCX archives, and invalid PDF headers. Verified that all return structured failure objects rather than uncaught crashes.
- **Boundary Limits:** Verified rejection of unsupported extensions (`.png`) and file-size exceeding threshold (`> 10 MB`).
- **Entity Extraction:** Verified email extraction with varying domains, 10-15 digit telephone detection (including standard parentheses formatting), and top-of-file candidate name extraction.

### B. Requirement Extractor (`tests/test_requirement_extractor.py` - 13 Tests)
- **Taxonomy Matching:** Verified detection of canonical skills (`Java`, `Spring Boot`, `PostgreSQL`).
- **Dynamic Job Title Inference:** Tested dynamic role detection (`Java Full Stack Developer`, `Python Developer`, `Frontend Developer`, `Data Analyst`, `Software Engineer`, `Cybersecurity Analyst`), explicit header labels (`Job Title: ...`, `Role: ...`, `Position: ...`), neutral fallback (`Custom Job Description`), and empty handling (`Not Specified`).
- **Case-Insensitivity:** Tested uppercase/lowercase variations (`PYTHON`, `DOCKER`, `aws`).
- **Alias Resolution:** Validated mapping of synonyms (`k8s` -> `Kubernetes`, `drf` -> `Django`, `sklearn` -> `Scikit-Learn`).
- **Boundary Precision:** Confirmed that partial-substring words (e.g., `good`, `algorithm`, `read`) do not match single/double letter tokens (`Go`, `R`, `C`).
- **Section Parsing:** Tested separation of job requirements into `required` versus `preferred` buckets.

### C. Matching & Ranking Engine (`tests/test_matcher.py` - 7 Tests)
- **Mathematical Integrity:** Verified that identical vectors yield cosine similarity of 1.0, and zero vectors yield 0.0 without division-by-zero exceptions.
- **Ranking Correctness:** Confirmed that a strong synthetic Java developer resume ranks above an unrelated marketing resume.
- **Score Boundaries:** Confirmed that all composite scores, text similarities, and skill scores strictly fall within $[0.0, 100.0]$.
- **Collision Resistance:** Confirmed that duplicate uploaded filenames receive unique internal IDs (`candidate_id`) and maintain distinct ranking positions.
- **Determinism:** Confirmed identical outputs across repeated executions with identical input data.

### D. Export & Security Validation (`tests/test_validation.py` - 4 Tests)
- **Formula Injection Mitigation:** Verified prepending of `'` on cells starting with `=`, `+`, `-`, `@`, `\t`.
- **Unicode Support:** Verified correct handling of special characters (e.g., `René Müller`).
- **Structure:** Verified valid RFC 4180 CSV generation with full header columns and failure state tracking.

### E. Integration & AppTest (`tests/test_integration.py` - 8 Tests)
- **Streamlit Startup:** Initialized the Streamlit application via `streamlit.testing.v1.AppTest` and verified zero runtime exceptions.
- **Job Description Loading & Clearing:** Tested that the "Load Sample Job Description" button and "Clear Job Description" button properly update `session_state["jd_textarea"]`.
- **Dynamic Job Title & State Synchronization:** Verified that loading, clearing, and typing job descriptions synchronizes job titles across all pages, updates processing badges to `Processing: Local`, and disables the Analyze button when invalid.
- **End-to-End Workflow:** Executed the end-to-end recruiter workflow on the synthetic resume collection.
- **Pandas-Independent Leaderboard:** Verified that data tables render cleanly without importing pandas or triggering Windows Application Control DLL errors.
- **Field Mapping & Sparse Text Warnings:** Verified candidate metadata alignment and sparse PDF (< 25 words) review warnings.
- **Multi-Page ATS Navigation:** Verified seamless navigation across all 3 enterprise workspaces: Candidates Overview, Screening Overview & Analytics, and Candidate Review Workspace.
