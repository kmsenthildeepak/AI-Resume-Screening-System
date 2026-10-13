import { HeroParallax, type ProductCardItem } from "@/components/ui/hero-parallax";

export const atsProducts: ProductCardItem[] = [
  {
    title: "Instant Multi-Format Resume Parsing",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1586281380349-632531db7ed4?q=80&w=800&auto=format&fit=crop",
    category: "Ingestion Engine",
    description: "Robust extraction from PDF, DOCX, and TXT resumes with full encoding recovery.",
  },
  {
    title: "Job Description Competency Matching",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1551836022-d5d88e9218df?q=80&w=800&auto=format&fit=crop",
    category: "JD Alignment",
    description: "Automated requirement mapping comparing mandatory skills with applicant qualifications.",
  },
  {
    title: "Pure-Python TF-IDF & Cosine Scoring",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=800&auto=format&fit=crop",
    category: "Matching Core",
    description: "Transparent, deterministic vector scoring without external API dependencies.",
  },
  {
    title: "Candidate Leaderboard & Ranking",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=800&auto=format&fit=crop",
    category: "Screening Analytics",
    description: "Dynamic top-tier ranking with status tags: Strong Match, Moderate, and Low Match.",
  },
  {
    title: "Explainable Recommendation Badges",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1507679799987-c73779587ccf?q=80&w=800&auto=format&fit=crop",
    category: "Decision Support",
    description: "Actionable hiring indicators (Advance to Interview, Review Skills, Low Priority).",
  },
  {
    title: "Skill Coverage & Keyword Density",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=800&auto=format&fit=crop",
    category: "Gap Analysis",
    description: "Granular breakdown of matching vs missing technical and soft skills.",
  },
  {
    title: "Deep-Dive Candidate Review Dossier",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?q=80&w=800&auto=format&fit=crop",
    category: "Recruiter Workspace",
    description: "Comprehensive profiles with extracted contact info, education, and raw resume view.",
  },
  {
    title: "Evidence Extraction & Context Quotes",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?q=80&w=800&auto=format&fit=crop",
    category: "Audit & Transparency",
    description: "Verifiable snippets linking applicant claims directly to source resume passages.",
  },
  {
    title: "Experience Timeline & Seniority Calibration",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1522071820081-009f0129c71c?q=80&w=800&auto=format&fit=crop",
    category: "Experience Profiling",
    description: "Multi-year career trajectory evaluation against role tenure requirements.",
  },
  {
    title: "100% Private On-Premise Processing",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1563986768609-322da13575f3?q=80&w=800&auto=format&fit=crop",
    category: "Enterprise Privacy",
    description: "Zero external cloud data transfer; GDPR/compliance-ready local execution.",
  },
  {
    title: "Cross-Navigation Session Preservation",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1552664730-d307ca884978?q=80&w=800&auto=format&fit=crop",
    category: "UX Architecture",
    description: "Retains job description, upload caches, and analytical states seamlessly.",
  },
  {
    title: "Executive Screening Overview Charts",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=800&auto=format&fit=crop",
    category: "Visual Reporting",
    description: "Score distribution histograms and pipeline velocity metrics for talent leads.",
  },
  {
    title: "One-Click Export & ATS Integration",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1542744094-3a31f272c490?q=80&w=800&auto=format&fit=crop",
    category: "Interoperability",
    description: "Export candidate dossiers to CSV, JSON, and standard HRIS schemas instantly.",
  },
  {
    title: "Real-Time Pipeline Filtering",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1531482615713-2afd69097998?q=80&w=800&auto=format&fit=crop",
    category: "Talent Search",
    description: "Dynamic threshold filtering by score, key skills, experience level, or status.",
  },
  {
    title: "Comprehensive 67-Point Automated Verification",
    link: "http://localhost:8501",
    thumbnail: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=800&auto=format&fit=crop",
    category: "Engineering Quality",
    description: "Enterprise test coverage validating tokenizer, parser, ranker, and UX flows.",
  },
];

export function HeroParallaxDemo() {
  return (
    <div className="bg-slate-950 min-h-screen text-slate-100 selection:bg-blue-600 selection:text-white">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 w-full border-b border-neutral-800/80 bg-slate-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6">
          <div className="flex items-center gap-3">
            <img
              src="/logo.svg"
              alt="AI Resume Screening System Logo"
              className="h-9 w-9 rounded-lg shadow-md shadow-blue-500/20 object-contain"
            />
            <div className="flex flex-col">
              <span className="text-sm font-bold tracking-tight text-white">AI Resume Screening System</span>
              <span className="text-[11px] text-neutral-400">Enterprise Candidate Intelligence</span>
            </div>
          </div>
          
          <nav className="flex items-center gap-4">
            <a
              href="http://localhost:8501"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs sm:text-sm font-semibold text-white shadow hover:bg-blue-500 transition-colors focus:ring-2 focus:ring-blue-400"
            >
              <span>Launch ATS Dashboard</span>
              <span className="inline-block transition-transform group-hover:translate-x-1">&rarr;</span>
            </a>
          </nav>
        </div>
      </header>

      {/* Main Aceternity Hero Parallax Section */}
      <main>
        <HeroParallax
          products={atsProducts}
          headerTitle="AI-Powered Resume Screening System"
          headerSubtitle="Screen resumes, match skills against job descriptions, and compare candidates using transparent, evidence-based ranking indicators."
          dashboardUrl="http://localhost:8501"
        />

        {/* Feature Detail Section for deep exploration */}
        <section id="features" className="relative z-20 border-t border-neutral-800 bg-slate-900/50 py-20 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-sky-400">
                Architectural Pillars
              </h2>
              <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Engineered for High-Velocity Talent Acquisition
              </p>
              <p className="mt-4 text-neutral-400 text-sm sm:text-base">
                Discover how our hybrid local matching architecture empowers hiring teams to screen hundreds of candidates in seconds with mathematically grounded transparency.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="rounded-2xl border border-neutral-800 bg-slate-950/60 p-6 backdrop-blur-sm">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 font-bold mb-4">
                  01
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Deterministic Scoring</h3>
                <p className="text-sm text-neutral-400 leading-relaxed">
                  Utilizes TF-IDF term weighting combined with cosine similarity and skill coverage ratios to generate objective, reproducible match scores without hallucination risk.
                </p>
              </div>

              <div className="rounded-2xl border border-neutral-800 bg-slate-950/60 p-6 backdrop-blur-sm">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 font-bold mb-4">
                  02
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Auditable Evidence Quotes</h3>
                <p className="text-sm text-neutral-400 leading-relaxed">
                  Every score breakdown highlights direct evidence snippets from candidate resumes alongside identified matched and missing skills, giving recruiters clear confidence.
                </p>
              </div>

              <div className="rounded-2xl border border-neutral-800 bg-slate-950/60 p-6 backdrop-blur-sm">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 font-bold mb-4">
                  03
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Zero-Leakage Privacy</h3>
                <p className="text-sm text-neutral-400 leading-relaxed">
                  Candidate resumes and proprietary job descriptions never leave your machine. Processing runs 100% locally in Python with no external cloud API requirements.
                </p>
              </div>
            </div>

            <div className="mt-16 text-center">
              <a
                href="http://localhost:8501"
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-4 text-base font-semibold text-white shadow-xl shadow-blue-500/20 hover:from-blue-500 hover:to-indigo-500 hover:shadow-blue-500/40 transition-all hover:-translate-y-0.5"
              >
                <span>Launch Interactive Screening Dashboard</span>
                <span>&rarr;</span>
              </a>
              <p className="mt-3 text-xs text-neutral-500">
                Running locally on Streamlit (Port 8501) &bull; 67 Automated Unit Tests Passing
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-900 bg-black py-8 px-4 text-center text-xs text-neutral-500">
        <p>&copy; {new Date().getFullYear()} AI Resume Screening System &bull; Enterprise Applicant Tracking System.</p>
        <p className="mt-1">Powered by Pure-Python NLP Engine &bull; Aceternity UI Parallax Architecture</p>
      </footer>
    </div>
  );
}


