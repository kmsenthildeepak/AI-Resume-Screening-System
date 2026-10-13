# AI Resume Screening System — Aceternity UI Hero Parallax Integration

This document outlines the architecture, setup instructions, and verification details for the Aceternity UI Hero Parallax landing page integrated into the AI Resume Screening System.

---

## 1. Architecture Overview

The system features a dual-tier architecture combining modern React presentation with an on-premise, secure Python NLP core:

```
AI_Resume_Screening_System/
├── app.py                      # Production Streamlit ATS App (Port 8501)
├── matcher.py                  # Pure-Python TF-IDF & Cosine Similarity Matcher
├── resume_parser.py            # Local PDF/DOCX/TXT Ingestion Engine
├── requirement_extractor.py    # Rule-based Skill & Requirement Extractor
├── tests/                      # Pytest Automated Test Suite (67 passing tests)
│
└── frontend/                   # Aceternity UI Hero Parallax Landing Page (Port 5173)
    ├── src/
    │   ├── components/
    │   │   ├── ui/
    │   │   │   └── hero-parallax.tsx    # Aceternity Parallax Component (motion/react)
    │   │   └── hero-parallax-demo.tsx   # 15 Custom ATS Feature Cards & CTA Header
    │   ├── lib/
    │   │   └── utils.ts                 # Class merger utility (clsx + tailwind-merge)
    │   ├── App.tsx
    │   └── index.css                    # Tailwind CSS directives & dark theme
    ├── package.json
    ├── tailwind.config.js
    └── vite.config.ts
```

---

## 2. Running Both Applications Locally

### Terminal 1: Streamlit ATS Dashboard
```powershell
cd E:\AI_Resume_Screening_System
.\.venv\Scripts\Activate.ps1
streamlit run app.py --server.port 8501
```
The Streamlit application will be active at: **`http://localhost:8501`**

### Terminal 2: Aceternity Hero Parallax Landing Page
```powershell
cd E:\AI_Resume_Screening_System\frontend
npm install
npm run dev
# or for production preview:
npm run build
npm run preview -- --port 5173
```
The Landing page will be active at: **`http://localhost:5173`**

---

## 3. Key Features of the Hero Parallax Landing Page

1. **Heading & Subtitle Aligned with ATS Purpose:**
   - **Heading:** *AI-Powered Resume Screening System*
   - **Subtitle:** *Screen resumes, match skills against job descriptions, and compare candidates using transparent, evidence-based ranking indicators.*
2. **Prominent Call to Action:**
   - Accessible button **Open Screening Dashboard** directly linking to `http://localhost:8501`.
   - Secondary sticky top bar button **Launch ATS Dashboard**.
3. **15 High-Fidelity ATS Domain Cards:**
   - Ingestion Engine (Multi-Format PDF/DOCX/TXT)
   - Job Description Competency Matching
   - Pure-Python TF-IDF & Cosine Scoring
   - Candidate Leaderboard & Ranking
   - Explainable Recommendation Badges
   - Skill Coverage & Keyword Density
   - Deep-Dive Candidate Review Dossier
   - Evidence Extraction & Context Quotes
   - Experience Timeline & Seniority Calibration
   - 100% Private On-Premise Processing
   - Cross-Navigation Session Preservation
   - Executive Screening Overview Charts
   - One-Click Export & ATS Integration
   - Real-Time Pipeline Filtering
   - Comprehensive 67-Point Automated Verification
4. **Motion & Accessibility:**
   - Powered by modern `motion/react` with spring damping physics.
   - Fully respects `prefers-reduced-motion` media queries.
   - Responsive across mobile (375px+), tablet, and desktop viewports.

---

## 4. Verification & Testing

- **Backend Pytest Suite:** All 67 unit and integration tests passing (`pytest tests`).
- **Frontend Build:** `npm run build` generates optimized bundle with 0 TypeScript errors.
- **Browser Automation:** Verified with Playwright headless inspection checking title, header, 15 cards, CTA link, scroll transforms, and mobile layout.
