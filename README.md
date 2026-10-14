# AI Resume Screening System

An enterprise-ready, AI-assisted decision-support resume screening and candidate ranking application built in Python and React. The system leverages Natural Language Processing (TF-IDF vectorization and Cosine Similarity), boundary-aware skill taxonomy extraction, and a multi-tier contextual evidence engine to objectively score, explain, and rank candidate resumes against job descriptions.

---

## 📌 Problem Statement & Objective

Recruitment teams receive hundreds of resumes for every posted position. Manually parsing and comparing resumes across disparate formats is repetitive, time-intensive, and prone to fatigue and unconscious bias.

The **AI Resume Screening System** serves as an interactive **decision-support workspace** designed to:
1. **Ingest & Parse Multi-Format Documents**: Extract structured text from **PDF, DOCX, and TXT** documents with robust error handling and file sanitization.
2. **Deconstruct Job Descriptions**: Automatically isolate Job Titles, Required Competencies, and Preferred / Bonus Qualifications.
3. **Pure-Python NLP & Similarity Engine**: Compute deterministic TF-IDF unigram/bigram vectors and cosine similarities without external C-extension binary dependencies (100% Windows Application Control compliant).
4. **Contextual Skill Evidence Layer**: Distinguish between buzzword-stuffed skills lists vs. verified, metric-backed impact in professional work experience.
5. **Deterministic, Bias-Free Ranking**: Rank candidates with strict score bounding \([0.0\%, 100.0\%]\) and deterministic multi-key tie-breaking, ensuring demographic identifiers (names, emails, phones, filenames) never influence candidate scores.
6. **Accessible ATS Recruiter Dashboard**: Multi-page Streamlit workspace featuring responsive candidate review tabs, accessible high-contrast raw document viewers, and sanitized CSV exports.
7. **Aceternity UI Hero Parallax Landing Page**: Modern React + TypeScript + Tailwind CSS marketing and landing experience.

> **Responsible AI Notice:** This system is an assistive screening tool. It does **not** make autonomous hiring decisions, does **not** reject candidates automatically, and explicitly excludes demographic attributes (gender, age, race, religion, etc.) from scoring algorithms.

---

## 🛠️ Technology Stack

| Layer | Technology | Rationale & Architectural Implementation |
|---|---|---|
| **Streamlit Workspace** | Python 3.11.9, Streamlit 1.32.2 | 3-Page ATS Recruiter Workspace (Screening Queue, Overview Metrics, Candidate Review) |
| **Landing Page** | React 18, Vite, TypeScript, Tailwind CSS, Framer Motion | Modern Aceternity UI Hero Parallax responsive landing experience in `frontend/` |
| **NLP & Scoring Engine** | Pure-Python Vectorizer & Cosine Math | Custom TF-IDF engine with pure Python math (`math.sqrt`), with optional Scikit-Learn fallback |
| **Document Parsers** | `pypdf`, `python-docx`, Python Standard Library | Resilient binary and text extractors with malformed document detection |
| **Evidence Extraction** | Regex & Section Segmenter | Multi-tier evidence classifier with quantified metric detection (`%`, `$`, scale numbers) |
| **Export Subsystem** | Standard `csv` | Formula-injection mitigated (`=`, `+`, `-`, `@`, `\t`, `\r`), UTF-8 encoded report generation |
| **Testing & QA** | `pytest`, Playwright | 79 automated pytest tests across 6 modules + headless browser UI verification |

---

## 📐 Scoring Formula & Mathematical Model

The system calculates a bounded composite match score between **0.0% and 100.0%** for each successfully parsed resume.

### 1. Composite Score

$$\text{Overall Score} = \left(W_{\text{text}} \times S_{\text{text}}\right) + \left(W_{\text{skill}} \times S_{\text{skill}}\right)$$

- **Default Weights:**
  - $W_{\text{text}} = 0.65$ (65% weight on TF-IDF textual similarity)
  - $W_{\text{skill}} = 0.35$ (35% weight on explicit skill taxonomy overlap)
  - Weights are validated and normalized: $W_{\text{text}} + W_{\text{skill}} = 1.0$. If invalid, NaN, infinite, negative, or all-zero weights are supplied, safe defaults are enforced.

### 2. Skill Overlap Calculation ($S_{\text{skill}}$)

Job descriptions are parsed into **Required Skills** ($R$) and **Preferred Skills** ($P$). Candidate resumes are evaluated against both sets:

- **When both Required and Preferred skills exist:**
  $$S_{\text{skill}} = W_{\text{req}} \times \left(\frac{|\text{Matched}_R|}{|R|}\right) + W_{\text{pref}} \times \left(\frac{|\text{Matched}_P|}{|P|}\right)$$
  - Default: $W_{\text{req}} = 0.80$ (80%) and $W_{\text{pref}} = 0.20$ (20%).
- **When only Required skills exist:**
  $$S_{\text{skill}} = \frac{|\text{Matched}_R|}{|R|}$$
- **When only Preferred skills exist:**
  $$S_{\text{skill}} = \frac{|\text{Matched}_P|}{|P|}$$
  *(Candidates never receive unearned credit for an empty required skills section).*
- **When no cataloged skills exist in the Job Description:**
  The system falls back gracefully to 100% TF-IDF textual similarity ($S_{\text{skill}} = S_{\text{text}}$).

### 3. Deterministic Multi-Key Tie Breaking

Candidates with identical overall scores are deterministically ranked using a stable tuple key:
1. `overall_score` (descending)
2. `matched_required_count` (descending)
3. `text_similarity` (descending)
4. `candidate_name` (case-insensitive alphabetical ascending)
5. `file_id` (lexicographical ascending)

Failed or unparseable resumes always receive an overall score of `0.0%` and are positioned at the bottom of the leaderboard with clear error diagnostics.

---

## 🔍 Explainable Skill Evidence Engine

To provide recruiters with transparent verification and expose keyword stuffing, the system parses resumes into structural sections (`work_experience`, `projects`, `skills`, `education`) and categorizes each matched skill into an **Evidence Tier**:

| Tier | Badge | Definition & Criteria |
|---|---|---|
| **Impact** | 🏆 `Impact` | Skill appears in work experience alongside quantifiable metrics (e.g. `25%`, `$1.2M`, `10x`, `500k`) or strong impact verbs (`optimized`, `scaled`, `reduced`, `delivered`). |
| **Work Experience** | ⚡ `Experience` | Skill demonstrated in professional job history and responsibilities without specific numerical metrics. |
| **Project** | 🛠️ `Project` | Skill demonstrated in portfolio projects, capstones, or open-source repositories. |
| **Skills List** | 📋 `Skills List` | Skill found solely in a summary skills inventory or comma-separated list. Flagged with a warning: *"Listed in skills summary only; no contextual work experience verified."* |
| **Mention Only** | ⚠️ `Mention` | Skill occurs casually in general resume body text without identifiable section context. |

> **Audit & Explanation Notice:** Evidence tiers, snippets, and Evidence Coverage percentages are strictly **explanatory and audit-focused**. They provide recruiters with qualitative verification and verbatim excerpts to audit claims, but do **not** mathematically modify the composite score or ranking order.

---

## 📂 Project Directory Structure

```text
AI_Resume_Screening_System/
├── app.py                      # Streamlit 3-page recruiter workspace
├── resume_parser.py            # Multi-format document parser (PDF, DOCX, TXT)
├── requirement_extractor.py    # JD parser, skill taxonomy, and evidence extractor
├── matcher.py                  # Pure-Python TF-IDF vectorizer, cosine similarity & ranking
├── exporter.py                 # Sanitized CSV generation with formula-injection guard
├── config.py                   # System constants, weights, and skill taxonomy dictionary
├── inspect_raw_resume.mjs      # Playwright browser inspection and visual QA script
├── requirements.txt            # Tested Python dependencies
├── pytest.ini                  # Pytest configuration
├── frontend/                   # React + TypeScript + Tailwind landing application
│   ├── src/                    # Hero Parallax component, UI cards, and styles
│   ├── package.json            # Vite, React, Framer Motion, Tailwind dependencies
│   └── vite.config.ts          # Vite build configuration
├── sample_resumes/             # Synthetic test resumes for demonstration and testing
│   ├── resume_01_strong_match.txt     # Senior Java / Backend engineer
│   ├── resume_02_partial_match.docx   # Full Stack engineer with partial match
│   ├── resume_03_unrelated.txt        # Marketing specialist (negative control)
│   └── resume_04_python_dev.pdf       # Python / Data engineer PDF
├── tests/                      # Automated test suite (79 tests)
│   ├── test_evidence.py               # Skill evidence tiers, metrics, and warnings (5 tests)
│   ├── test_fairness.py               # Anti-bias and demographic neutrality (2 tests)
│   ├── test_integration.py            # Streamlit workflows, queue, and navigation (28 tests)
│   ├── test_matcher.py                # Pure-Python TF-IDF, scoring math, tie-breaking (11 tests)
│   ├── test_requirement_extractor.py  # JD sections, skill boundary matching (14 tests)
│   ├── test_resume_parser.py          # PDF, DOCX, TXT parsers & entity extraction (15 tests)
│   └── test_validation.py             # CSV sanitization, formula safety, Unicode (4 tests)
└── docs/                       # Project reports, user guides, and architecture specs
```

---

## 🚀 Setup & Execution Guide (Windows / PowerShell)

### Prerequisites
- Windows 10 / 11
- Python 3.11+
- Node.js 18+ (for React landing page and Playwright verification)

### 1. Streamlit ATS Application

```powershell
# 1. Navigate to project root
cd E:\AI_Resume_Screening_System

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch Streamlit Recruiter Workspace
streamlit run app.py
```
Access the application at `http://localhost:8501`.

### 2. React Landing Page (Hero Parallax)

```powershell
# 1. Navigate to frontend directory
cd E:\AI_Resume_Screening_System\frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev

# 4. Or build for production
npm run build
```
Access the landing page at `http://localhost:5173`.

---

## 🧪 Automated Testing & Verification

Run the full automated pytest suite:

```powershell
pytest
```

**Results:**
- **79 passed in ~5.9s**
- `tests/test_evidence.py`: Validates evidence tiering, metric detection, and unverified skill warnings.
- `tests/test_fairness.py`: Confirms candidate names, emails, and demographic attributes do not skew scores.
- `tests/test_integration.py`: End-to-end tests for all 10 recruiter workflows, queue retention, and candidate display.
- `tests/test_matcher.py`: Validates pure-Python TF-IDF, cosine similarity, weight normalization, and determinism.
- `tests/test_requirement_extractor.py`: Tests boundary-aware skill matching (e.g., `Go`, `R`, `C++`, `C#`, `.NET`) and JD sectioning.
- `tests/test_resume_parser.py`: Tests PDF, DOCX, TXT document extraction, malformed files, and size limits.
- `tests/test_validation.py`: Tests CSV export sanitization, formula safety, and UTF-8 encoding.

### Visual & Browser Contrast Inspection

To verify DOM rendering, candidate switching, and accessible contrast in both Light and Dark color schemes:

```powershell
node inspect_raw_resume.mjs
```

Screenshots are generated automatically at `raw_resume_light.png` and `raw_resume_dark.png`.

---

## 🔒 Security, Privacy & Fairness Safeguards

1. **Anti-Bias Guarantee**: Names, emails, phone numbers, and filenames are explicitly stripped from text before TF-IDF vectorization. Demographic characteristics (race, gender, nationality, age) are never collected or scored.
2. **Formula Injection Sanitization**: All exported CSV cells starting with spreadsheet execution triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) are automatically escaped with leading single quotes (`'`).
3. **Local In-Memory Execution**: Resumes are parsed and scored entirely in local memory. No resume text, contact details, or candidate data are transmitted to external cloud APIs or third-party servers.
4. **WDAC & Windows Integrity Compliance**: The scoring and ranking engine runs entirely on standard library Python data structures and pure-Python math, removing strict dependencies on native C-extension DLLs blocked by corporate Application Control policies.
