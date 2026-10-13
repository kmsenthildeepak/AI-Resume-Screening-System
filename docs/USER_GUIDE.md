# Recruiter User Guide: Enterprise ATS Screening Workspace

Welcome to the **AI Resume Screening System (Enterprise ATS)**. This operational manual provides end-to-end instructions for talent acquisition professionals, recruitment teams, and hiring managers.

---

## 🚀 Quick Start Guide

### 1. Launching the Dashboard
Open PowerShell in the application directory and run:
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
Your default web browser will automatically open to `http://localhost:8501`.

### 2. Multi-Page Enterprise Navigation
Use the persistent left sidebar navigation to transition between three purpose-built workspaces:
1. **Candidates**: Upload resumes, paste job descriptions, filter candidate database, and export CSV reports.
2. **Screening Overview**: Analytical dashboard covering cohort metrics, competency coverage bars, and side-by-side match comparisons.
3. **Candidate Review**: Split-panel evaluation workspace with left queue selector and right dossier (contact, scoring, matched/missing skills, evidence citations, raw text).

---

## 📋 Step-by-Step Screening Workflow

### Step 1: Input Job Description & Upload Resumes (Candidates Tab)
1. In the **Job Description Setup** card:
   - Paste job requirements or click **"Load Sample Job Description"** to load a standard Java Full Stack Developer template.
   - The system detects role competencies automatically and renders them as subtle tags.
2. In the **Resume Upload & Screening Queue** card:
   - Drag and drop resumes in `.pdf`, `.docx`, or `.txt` format (up to 10 MB each).
   - Click **"Analyze & Rank Candidates"**.
3. In the persistent **Sidebar**:
   - Optionally adjust the **Text Similarity Weight** slider (default: 65% text similarity, 35% competency match).

### Step 2: Filter and Inspect Candidate Database (Candidates Tab)
1. Use the search box to find candidates by name, email, or filename.
2. Filter candidates by status (`Ready for review`, `Review notice`, `Extraction failed`) or minimum score (`>= 40%`, `>= 25%`, `< 25%`).
3. Inspect candidate ranking, overall score with progress bar, text similarity, skill match, and matched skill badges.
4. Click **"Export CSV"** to download `candidate_screening_report.csv` (protected against CSV formula injection).

### Step 3: Assess Cohort Competency Coverage (Screening Overview Tab)
1. Navigate to **Screening Overview** via the left sidebar.
2. Review high-level metrics: Candidates Evaluated, Average Match Score, Competency Matches, and candidates Requiring Review.
3. Review the **Required Competency Coverage** progress bars showing the exact percentage and candidate count possessing each required skill.
4. Inspect role criteria and the **Candidate Match Comparison** table.

### Step 4: Conduct Deep-Dive Evaluation (Candidate Review Tab)
1. Navigate to **Candidate Review** in the sidebar.
2. Click any applicant in the **Candidate Queue** list on the left.
3. In the right dossier panel, explore four detailed tabs:
   - **Overview & Contact**: Candidate email, phone, filename, composite match, and plain-English score explanation.
   - **Skills Alignment**: Matched role competencies (green badges) vs. missing competencies (grey badges).
   - **Evidence Quotes**: Extracted education credentials and work experience snippets with source context.
   - **Raw Document**: Scrollable preview of extracted text.

---

## 🛡️ Security, Privacy & Constraints

- **100% Local Execution:** Parsing and NLP vectorization occur entirely in local memory; no candidate data is transmitted externally.
- **Pandas-Independent Rendering:** Built for enterprise Windows Application Control environments without native binary DLL dependencies.
- **Formula Injection Defense:** All CSV export cells prepended with dangerous prefixes (`=`, `+`, `-`, `@`) are sanitized.
- **Decision-Support Guardrail:** The system ranks and flags candidates to assist human recruiters. It never auto-rejects candidates.

---

## ⚖️ Ethical Guidelines for Recruiters

- **Inspect Original Resumes:** Always review the candidate's original resume before scheduling interviews or making decisions.
- **Sparse Text Alerts:** Candidates flagged with "Review notice" (e.g. scanned or image-based PDFs) have limited extractable text and require manual inspection.
- **Transferable Skills:** Unconventional phrasing may lower keyword similarity despite strong real-world qualifications.
