# Academic Internship Project Report: AI Resume Screening System

**Course / Internship Track:** Artificial Intelligence, Machine Learning & NLP Applications  
**Project Title:** AI-Powered Resume Screening & Candidate Ranking System  
**Author / Intern:** Machine Learning & NLP Engineering Pair  
**Development Environment:** Python 3.11.9 on Microsoft Windows  

---

## 1. Abstract

In modern talent acquisition, organizations face massive application volumes for open positions. Manual resume screening is labor-intensive, repetitive, and vulnerable to human fatigue and unconscious cognitive bias. This project delivers an automated, transparent, and ethically grounded **AI Resume Screening System** developed in Python and Streamlit. The application ingests job descriptions alongside candidate resumes in PDF, DOCX, and TXT formats. It performs automated information extraction (contact details, technical competencies, education credentials, and work history indicators) and applies natural language processing (Term Frequency-Inverse Document Frequency vectorization with Cosine Similarity) coupled with a canonical skill taxonomy to rank candidates objectively. Experimental validation across synthetic candidate benchmarks demonstrates strict rank ordering, transparent scoring breakdowns, and reliable CSV report generation.

---

## 2. Introduction & Problem Statement

### 2.1 The Recruitment Challenge
Recruiting departments frequently receive hundreds of resumes per job opening. Reviewing individual submissions manually creates substantial bottlenecks:
- **Time Inefficiency:** Recruiters spend an average of 6–10 seconds per resume during initial sweeps, risking oversight of qualified applicants.
- **Inconsistent Standards:** Human evaluation thresholds vary depending on reviewer fatigue, subjective preferences, and time constraints.
- **Unconscious Bias:** Subjective screening can inadvertently favor or disadvantage applicants based on extraneous demographic cues.

### 2.2 Objective
The primary objective of this project is to develop an automated decision-support system that:
1. Normalizes and extracts text from unstructured documents across standard enterprise formats (**PDF**, **DOCX**, **TXT**).
2. Performs keyword and entity recognition to identify candidate contact details and skill sets.
3. Computes mathematical relevance between job descriptions and resumes using TF-IDF n-gram vectorization and vector cosine similarity.
4. Computes explicit skill overlap against a curated competency taxonomy with alias support.
5. Displays rank-ordered candidates through an interactive dashboard with verifiable qualification evidence.
6. Exports sanitized screening results for auditability and recruiter collaboration.

---

## 3. Existing System Limitations vs. Proposed System

| Feature | Legacy / Manual Screening | Existing Black-Box Systems | Proposed AI Screening System |
|---|---|---|---|
| **Speed & Scalability** | Manual; hours per candidate batch | Fast, cloud-dependent | Near-instantaneous, local execution |
| **Transparency** | Highly subjective | Black-box neural models; opaque decisions | Fully explainable formula (TF-IDF + Skill Overlap) |
| **Privacy & Security** | Data handled manually | Transmits private CVs to external APIs | 100% On-Premise; zero third-party transmission |
| **Protected Attribute Safety**| Subject to cognitive bias | Risk of demographic feature leakage | Explicitly discards non-job demographic features |
| **Evidence Traceability** | Notes kept manually | Scores without evidence citations | Surfaces extracted education & work history quotes |

---

## 4. System Architecture & Methodology

### 4.1 Architecture Pipeline
```text
[ Job Description ] ───► [ Requirement Extractor ] ──► Job Skill Taxonomy Set
                                                                 │
[ Multi-Format Resumes ] ──► [ Multi-Format Parser ] ──► Candidate Text & Metadata
(PDF, DOCX, TXT)                                                 │
                                                                 ▼
                                                  [ NLP Matching Engine ]
                                                  ├─ TF-IDF Vectorization (1-2 ngrams)
                                                  ├─ Pure NumPy Cosine Similarity
                                                  └─ Skill Taxonomy Overlap Scoring
                                                                 │
                                                                 ▼
                                                  [ Candidate Ranking Engine ]
                                                                 │
                                           ┌─────────────────────┴─────────────────────┐
                                           ▼                                           ▼
                                [ Streamlit Dashboard ]                     [ Sanitized CSV Export ]
```

### 4.2 Mathematical Scoring Formulation
Relevance is formulated as a linear combination of full-text contextual relevance and explicit competency alignment:

$$\text{Overall Match Score} = \left(W_{\text{text}} \times S_{\text{TF-IDF}}\right) + \left(W_{\text{skill}} \times S_{\text{Skill}}\right)$$

Where:
- $W_{\text{text}} = 0.65$ (Configurable weighting for textual similarity)
- $W_{\text{skill}} = 0.35$ (Configurable weighting for skill overlap)
- $S_{\text{TF-IDF}} = \cos(\vec{q}, \vec{d}) = \frac{\vec{q} \cdot \vec{d}}{\|\vec{q}\|_2 \|\vec{d}\|_2}$ where $\vec{q}$ is the job description vector and $\vec{d}$ is the resume vector.
- $S_{\text{Skill}}$ evaluates required ($R$) and preferred ($P$) skill overlap:
  $$S_{\text{Skill}} = 0.80 \times \left(\frac{|R \cap C|}{|R|}\right) + 0.20 \times \left(\frac{|P \cap C|}{|P|}\right)$$

---

## 5. Experimental Results & Verification

Testing was conducted using synthetic benchmark resumes across three candidate profiles for a Senior Java Backend Developer role:
1. **Candidate 1 (Alex Morgan - Strong Match):** Experienced Java engineer with Spring Boot, Microservices, Docker, Kafka, and PostgreSQL.
2. **Candidate 2 (Jordan Lee - Partial Match):** Web developer with Python, Django, Docker, and MySQL, with general Java exposure.
3. **Candidate 3 (Taylor Smith - Unrelated):** Senior marketing and SEO specialist with zero software engineering competencies.

### Benchmark Scoring Results:
| Candidate | Format | Matched Skills | Overall Score | Text Sim | Skill Match | Assigned Rank |
|---|---|---|---|---|---|---|
| Alex Morgan | TXT | 14 / 14 | **51.68%** | 25.65% | 100.0% | **#1** |
| Jordan Lee | DOCX | 6 / 14 | **27.51%** | 13.60% | 53.33% | **#2** |
| Taylor Smith | TXT | 0 / 14 | **1.26%** | 1.95% | 0.00% | **#3** |

### Automated Quality Assurance:
The comprehensive automated test suite (`pytest`) executed **42 test cases** with a 100% pass rate:
- Multi-format extraction (PDF, DOCX, TXT): 15 tests passed
- Skill taxonomy & word boundary detection: 9 tests passed
- NLP scoring constraints & determinism: 7 tests passed
- CSV formula sanitization & Unicode: 4 tests passed
- Streamlit UI, AppTest workflows & multi-page ATS navigation: 7 tests passed

### UI/UX Architecture:
The interface is structured as a complete three-tier enterprise ATS recruitment workspace:
1. **Candidates Overview:** Central candidate database with search, status and score filtering, full-width responsive HTML data table, resume queue, and sanitized CSV exporter.
2. **Screening Overview & Analytics:** Cohort analytics dashboard presenting match metrics, role criteria, horizontal competency coverage bars, and side-by-side candidate comparison tables.
3. **Candidate Review Workspace:** Split-panel evaluation view featuring a persistent left candidate queue and a detailed right dossier with four tabbed views (Overview & Contact, Skills Alignment, Evidence Quotes, and Raw Document preview).

---

## 6. Responsible AI & Ethical Safeguards

1. **Strictly Assistive Decision Support:** The system does not make autonomous employment determinations; it ranks textual alignment to assist human recruiters.
2. **Exclusion of Protected Attributes:** Algorithms do not extract or evaluate demographic variables such as race, ethnicity, religion, caste, gender, age, disability status, or candidate photographs.
3. **Transparent Evidence Attribution:** Recruiter interfaces display the exact detected skills, missing requirements, and verbatim snippets from candidate resumes for verification.
4. **Data Sovereignty & Privacy:** No candidate documents are permanently stored on disk or transmitted to third-party cloud APIs.

---

## 7. Limitations & Future Scope

### Limitations
- **OCR Not Included:** Scanned images or flattened PDFs lacking embedded text layers cannot be extracted without an external OCR binary (e.g., Tesseract).
- **Keyword Dependency:** While synonyms and aliases are mapped via taxonomy, novel technologies outside the taxonomy contribute solely via general TF-IDF similarity.

### Future Scope
- Integration of an offline transformer model (e.g., sentence-transformers) for semantic embedding similarity.
- Configurable domain taxonomies for medical, legal, and finance industries.
- Multi-language resume parsing support for global enterprise deployments.

---

## 8. References
1. Scikit-Learn Documentation: *Feature Extraction & TF-IDF Vectorization* (scikit-learn.org).
2. PyPDF Documentation: *Text Extraction from PDF Documents* (pypdf.readthedocs.io).
3. Python-docx: *Reading and Creating Microsoft Word Documents in Python* (python-docx.readthedocs.io).
4. Streamlit Documentation: *Interactive Data Applications* (docs.streamlit.io).
