# AI Resume Screening System

An AI-powered decision-support resume screening and candidate ranking application built in Python. The system utilizes Natural Language Processing (TF-IDF vectorization and Cosine Similarity), regex-based contact and entity extraction, and a standardized skill taxonomy to objectively score and rank candidate resumes against a supplied job description.

---

## 📌 Problem Statement & Objective

Recruitment teams receive hundreds of resumes for every posted position. Manually parsing and comparing resumes is repetitive, time-intensive, and prone to fatigue and unconscious bias. 

The **AI Resume Screening System** serves as an interactive **decision-support tool** to:
1. Parse resumes across diverse file formats (**PDF, DOCX, TXT**).
2. Extract candidate contact details, technical skills, education degrees, and experience snippets.
3. Analyze job descriptions for required vs. preferred competencies.
4. Calculate composite match scores using **TF-IDF textual similarity** and **skill taxonomy overlap**.
5. Rank candidates objectively while providing verifiable evidence snippets.
6. Export sanitized, publication-ready **CSV reports** for recruiter collaboration.

> **Responsible AI Notice:** This system is an assistive screening tool. It does **not** make autonomous hiring decisions, does **not** reject candidates automatically, and explicitly excludes demographic attributes (gender, age, race, religion, etc.) from scoring algorithms.

---

## 🛠️ Technology Stack

| Component | Technology | Rationale & Implementation Details |
|---|---|---|
| **Language** | Python 3.11.9 | High-performance, broad library compatibility |
| **User Interface** | Streamlit | Enterprise 3-Page ATS Workspace (Candidates, Screening Overview, Review) |
| **Rendering** | Clean Custom HTML/CSS | 100% Pandas-independent rendering compatible with Windows Application Control |
| **NLP & Matching** | Scikit-Learn & NumPy | Scikit-Learn `TfidfVectorizer` (unigrams + bigrams) with pure NumPy cosine similarity |
| **Document Parsers** | `pypdf`, `python-docx`, Standard `open` | Robust text extraction from PDF, Word (.docx), and plain text (.txt) |
| **Export Engine** | Python `csv` (Standard Library) | Formula-injection mitigated, UTF-8 encoded spreadsheet generation |
| **Testing Suite** | `pytest` | 42 automated tests covering unit parsing, NLP scoring, and multi-page UI |

---

## 📐 Scoring Formula & Matching Algorithm

The system computes a composite relevance score between 0% and 100% for each successfully parsed resume:

$$\text{Overall Score} = (W_{\text{text}} \times \text{Text Similarity}) + (W_{\text{skill}} \times \text{Skill Match Score})$$

- **Default Weights:**
  - $W_{\text{text}} = 65\%$ (Full-text contextual relevance via TF-IDF Cosine Similarity)
  - $W_{\text{skill}} = 35\%$ (Explicit skill taxonomy overlap)
  - *Weights are recruiter-adjustable in real time via the application sidebar.*
- **Skill Overlap Calculation:**
  - If job requirements include preferred skills:
    $$\text{Skill Score} = 0.80 \times \left(\frac{\text{Matched Required}}{\text{Total Required}}\right) + 0.20 \times \left(\frac{\text{Matched Preferred}}{\text{Total Preferred}}\right)$$
  - If no preferred skills are delineated:
    $$\text{Skill Score} = \frac{\text{Matched Skills}}{\text{Total Job Skills}}$$
  - **Graceful Fallback:** If the job description contains no cataloged skills, the system falls back to 100% TF-IDF textual similarity.

---

## 📂 Project Directory Structure

```text
AI_Resume_Screening_System/
├── app.py                      # Main Streamlit web application & recruiter dashboard
├── resume_parser.py            # Multi-format document parser (PDF, DOCX, TXT)
├── requirement_extractor.py    # Job description parser & canonical skill taxonomy
├── matcher.py                  # TF-IDF vectorizer, cosine similarity & ranking pipeline
├── exporter.py                 # Safe CSV generation with formula-injection mitigation
├── config.py                   # System constants, scoring weights, and skill dictionaries
├── requirements.txt            # Tested, reproducible Python dependencies
├── pytest.ini                  # Pytest configuration and Python path setup
├── .gitignore                  # Git ignore rules for virtualenvs, caches, and temp files
├── sample_resumes/             # Synthetic test resumes
│   ├── resume_01_strong_match.txt     # Strong Java backend match (Score ~51.7%, 100% skills)
│   ├── resume_02_partial_match.docx   # Partial full-stack match (Score ~27.5%, 53% skills)
│   ├── resume_03_unrelated.txt        # Unrelated marketing resume (Score ~1.3%, 0% skills)
│   └── resume_04_python_dev.pdf       # Text-based PDF sample resume
├── tests/                      # Automated test suite (42 tests)
│   ├── test_resume_parser.py          # Document parsing, boundaries, and entity extraction
│   ├── test_requirement_extractor.py  # Skill extraction, aliases, and false-positive limits
│   ├── test_matcher.py                # Cosine similarity, score boundaries, determinism
│   ├── test_validation.py             # CSV sanitization, formula safety, and Unicode
│   └── test_integration.py            # Streamlit AppTest & multi-page recruiter workflows
├── docs/                       # Comprehensive documentation
│   ├── PROJECT_REPORT.md              # Academic internship project report
│   ├── USER_GUIDE.md                  # Recruiter walkthrough and operation manual
│   ├── TEST_REPORT.md                 # Complete pytest execution results & audit log
│   └── ARCHITECTURE.md                # System design and dataflow diagrams
└── screenshots/                # Visual reference guides & UI layout diagrams
```

---

## 🚀 Setup & Installation (Windows)

### Prerequisites
- Windows 10 / 11
- Python 3.11+ installed

### Step-by-Step Installation

1. **Open PowerShell** in the project directory:
   ```powershell
   cd E:\AI_Resume_Screening_System
   ```

2. **Activate the Virtual Environment**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   *(Or create a new environment: `python -m venv .venv` followed by activation)*

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Launch the Application**:
   ```powershell
   streamlit run app.py
   ```
   The application will launch in your default web browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Run the full pytest suite with verbose output:

```powershell
pytest
```

**Test Suite Coverage Summary:**
- **37 passed in ~1.7s**
- `test_resume_parser.py`: 15 unit tests covering TXT, DOCX, PDF, empty files, size limits, and entity regexes.
- `test_requirement_extractor.py`: 9 unit tests verifying alias mappings, word boundaries, and sections.
- `test_matcher.py`: 7 tests validating score ranges [0.0, 100.0], determinism, and duplicate file handling.
- `test_validation.py`: 4 tests validating CSV formula injection mitigation and UTF-8 encoding.
- `test_integration.py`: 2 end-to-end tests validating the full candidate screening pipeline and Streamlit UI initialization.

---

## 🔒 Security, Privacy & Responsible AI

- **No Third-Party Cloud Transmissions:** All document parsing and NLP scoring run 100% locally on your machine. No resumes or job descriptions are transmitted across external networks.
- **Formula Injection Mitigation:** Cell values starting with spreadsheet command characters (`=`, `+`, `-`, `@`, `\t`) are automatically escaped in exported CSVs.
- **Privacy By Design:** Full resume contents are not logged or stored permanently; analysis happens purely in session memory.
- **Anti-Bias:** Protected attributes (race, gender, age, disability, address) are never extracted or factored into candidate rankings.

---

## 🛡️ Windows Environment Diagnostics Note

During initial setup on Windows, importing `pandas` failed with:
`ImportError: DLL load failed while importing index: An Application Control policy has blocked this file.`

**Diagnostic Cause:**
Windows Defender Application Control (WDAC / Device Guard) enforces user-mode code integrity policies that block unsigned or unwhitelisted native binary C-extensions (`.pyd` files).

**Engineered Solution:**
Rather than weakening Windows security or requiring administrative changes:
1. The CSV export and tabular display modules were engineered using Python's **standard library `csv`** and native Python data structures (`list[dict]`).
2. The NLP pipeline pairs **Scikit-Learn `TfidfVectorizer`** with **NumPy linear algebra** for cosine similarity calculations.
3. The system operates with **100% functionality and test coverage** without any reliance on blocked DLLs.
