import React, { useState, useRef, useEffect } from "react";
import {
  Upload,
  FileText,
  X,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Download,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Sliders,
  Check,
  Briefcase,
  Layers,
  GraduationCap,
  Clock,
  ExternalLink,
} from "lucide-react";
import {
  screenResumes,
  fetchSampleJobDescription,
  downloadScreeningCsv,
  checkApiHealth,
  extractSkillSnippets,
  extractSkillTier,
  getStreamlitCandidatesUrl,
  type ScreeningResponse,
  type CandidateResult,
  API_BASE_URL,
} from "../services/api";
import { ErrorBoundary } from "./error-boundary";

const FALLBACK_SAMPLE_JD = `Role: Java Full Stack Developer

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
- Familiarity with CI/CD automation tools like Jenkins or GitHub Actions.`;

export function ScreeningWorkspace() {
  const [jobDescription, setJobDescription] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ScreeningResponse | null>(null);
  const [expandedCandidate, setExpandedCandidate] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  // Configurable weights
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [weightTextSim, setWeightTextSim] = useState(0.65);
  const [weightSkillMatch, setWeightSkillMatch] = useState(0.35);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Check backend health on mount
  useEffect(() => {
    let isMounted = true;
    checkApiHealth()
      .then(() => {
        if (isMounted) setBackendStatus("online");
      })
      .catch(() => {
        if (isMounted) setBackendStatus("offline");
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFiles: File[]) => {
    const validExtensions = [".pdf", ".docx", ".txt"];
    const accepted: File[] = [];
    const rejected: string[] = [];

    for (const f of newFiles) {
      const ext = f.name.slice(f.name.lastIndexOf(".")).toLowerCase();
      if (!validExtensions.includes(ext)) {
        rejected.push(f.name);
        continue;
      }
      // Avoid duplicate filenames
      if (!files.some((existing) => existing.name === f.name && existing.size === f.size)) {
        accepted.push(f);
      }
    }

    if (rejected.length > 0) {
      setError(`Some files were skipped because only PDF, DOCX, and TXT are supported: ${rejected.join(", ")}`);
    } else {
      setError(null);
    }

    if (accepted.length > 0) {
      setFiles((prev) => [...prev, ...accepted]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = () => {
    setFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const loadSampleJd = async () => {
    setError(null);
    try {
      const data = await fetchSampleJobDescription();
      setJobDescription(data.sample_job_description);
      setBackendStatus("online");
    } catch {
      // Fallback to client-side constant if API call failed
      setJobDescription(FALLBACK_SAMPLE_JD);
    }
  };

  const handleScreenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) {
      setError("Please upload at least one resume document (.pdf, .docx, or .txt).");
      return;
    }
    if (jobDescription.trim().length < 30) {
      setError("Job description must contain at least 30 characters for accurate matching.");
      return;
    }

    setError(null);
    setIsLoading(true);
    setLoadingStage("Uploading candidate resumes...");

    try {
      // Stage sequence feedback
      setTimeout(() => setLoadingStage("Parsing document text and extracting contact info..."), 500);
      setTimeout(() => setLoadingStage("Extracting skills and computing pure-Python TF-IDF vectors..."), 1200);
      setTimeout(() => setLoadingStage("Calculating evidence coverage and final composite scores..."), 1800);

      const response = await screenResumes(
        jobDescription.trim(),
        files,
        weightTextSim,
        weightSkillMatch
      );

      setResults(response);
      setBackendStatus("online");
      setExpandedCandidate(response.results.length > 0 ? response.results[0].candidate_id : null);

      // Smooth scroll to results
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 300);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Screening request failed";
      setError(
        `${msg}. Make sure the FastAPI backend is running (uvicorn api:app --reload --port 8000) or check VITE_API_BASE_URL.`
      );
      setBackendStatus("offline");
    } finally {
      setIsLoading(false);
      setLoadingStage("");
    }
  };

  const handleDownloadCsv = async () => {
    if (!results) return;
    setIsExporting(true);
    try {
      await downloadScreeningCsv(results.screening_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to export CSV report";
      setError(msg);
    } finally {
      setIsExporting(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getScoreBadge = (score: number, success: boolean) => {
    if (!success) {
      return { label: "Parse Error", color: "bg-red-500/10 text-red-400 border-red-500/30" };
    }
    if (score >= 75) {
      return { label: "Strong Match", color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" };
    }
    if (score >= 50) {
      return { label: "Moderate Match", color: "bg-amber-500/10 text-amber-400 border-amber-500/30" };
    }
    return { label: "Low Match", color: "bg-slate-500/10 text-slate-400 border-slate-500/30" };
  };

  const getMedalColor = (rank: number) => {
    if (rank === 1) return "bg-amber-400 text-slate-950 font-black shadow-amber-400/30 shadow-lg";
    if (rank === 2) return "bg-slate-200 text-slate-950 font-bold shadow-slate-300/20 shadow-md";
    if (rank === 3) return "bg-amber-700 text-white font-bold";
    return "bg-neutral-800 text-neutral-300 font-medium";
  };

  return (
    <section id="screening" className="relative z-20 bg-slate-950 py-16 px-4 sm:px-6 lg:px-8 border-t border-neutral-800">
      <div className="mx-auto max-w-7xl">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-400 mb-4 backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Interactive Screening Engine</span>
            <span
              className={`h-2 w-2 rounded-full ${
                backendStatus === "online"
                  ? "bg-emerald-400 animate-pulse"
                  : backendStatus === "offline"
                  ? "bg-rose-500"
                  : "bg-amber-400"
              }`}
              title={`API Backend: ${backendStatus}`}
            />
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Screen & Rank Resumes in Real Time
          </h2>
          <p className="mt-3 text-neutral-400 text-sm sm:text-base leading-relaxed">
            Provide your target job description and upload applicant resumes. The pure-Python NLP engine extracts
            qualifications, evaluates TF-IDF cosine similarity, and maps canonical skill evidence instantly.
          </p>
        </div>

        {/* Backend Status Warning (if offline) */}
        {backendStatus === "offline" && (
          <div className="mb-8 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-amber-200 text-sm flex items-start gap-3 max-w-4xl mx-auto">
            <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-amber-300">FastAPI Backend Service Offline</p>
              <p className="text-xs text-amber-200/80">
                To run live screening locally, start the API service with:{" "}
                <code className="bg-black/40 px-1.5 py-0.5 rounded text-amber-300 font-mono">
                  .venv\Scripts\python.exe -m uvicorn api:app --reload --port 8000
                </code>
                . (API Base URL: {API_BASE_URL})
              </p>
            </div>
          </div>
        )}

        {/* Screening Input Form */}
        <form onSubmit={handleScreenSubmit} className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Column: Job Description (5 cols) */}
            <div className="lg:col-span-5 flex flex-col rounded-2xl border border-neutral-800 bg-slate-900/60 p-6 backdrop-blur-sm shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <label htmlFor="jd-input" className="text-sm font-semibold text-white flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-blue-400" />
                  Target Job Description
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={loadSampleJd}
                    className="text-xs text-sky-400 hover:text-sky-300 font-medium transition-colors cursor-pointer"
                  >
                    Load Sample JD
                  </button>
                  {jobDescription && (
                    <button
                      type="button"
                      onClick={() => setJobDescription("")}
                      className="text-xs text-neutral-400 hover:text-neutral-200 transition-colors cursor-pointer"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              <textarea
                id="jd-input"
                rows={12}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the target job description here (minimum 30 characters)..."
                className="w-full flex-grow rounded-xl border border-neutral-800 bg-slate-950/80 p-3.5 text-xs sm:text-sm text-slate-100 placeholder-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors resize-none font-mono leading-relaxed"
              />

              <div className="mt-3 flex items-center justify-between text-xs text-neutral-400">
                <span>
                  Length: <span className="text-white font-medium">{jobDescription.trim().length}</span> chars
                </span>
                <span className={jobDescription.trim().length >= 30 ? "text-emerald-400" : "text-amber-400"}>
                  {jobDescription.trim().length >= 30 ? "✓ Valid JD Length" : "Min. 30 chars required"}
                </span>
              </div>
            </div>

            {/* Right Column: Multi-File Ingestion (7 cols) */}
            <div className="lg:col-span-7 flex flex-col rounded-2xl border border-neutral-800 bg-slate-900/60 p-6 backdrop-blur-sm shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  Candidate Resumes (.pdf, .docx, .txt)
                </span>
                {files.length > 0 && (
                  <button
                    type="button"
                    onClick={clearAllFiles}
                    className="text-xs text-rose-400 hover:text-rose-300 transition-colors cursor-pointer"
                  >
                    Clear All ({files.length})
                  </button>
                )}
              </div>

              {/* Drag & Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-all ${
                  isDragging
                    ? "border-blue-500 bg-blue-500/10"
                    : "border-neutral-700 bg-slate-950/50 hover:border-neutral-600 hover:bg-slate-950/80"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileInputChange}
                  className="hidden"
                />
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10 text-blue-400 mb-3">
                  <Upload className="w-6 h-6" />
                </div>
                <p className="text-sm font-medium text-white">
                  Click to select resumes or drag & drop files here
                </p>
                <p className="mt-1 text-xs text-neutral-400">
                  Supports PDF (extractable text), DOCX, and TXT (up to 10 MB each)
                </p>
              </div>

              {/* Uploaded Files Queue */}
              {files.length > 0 ? (
                <div className="mt-4 flex-grow overflow-y-auto max-h-56 pr-1 space-y-2">
                  <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">
                    Active Screening Queue ({files.length} document{files.length === 1 ? "" : "s"})
                  </p>
                  {files.map((file, idx) => (
                    <div
                      key={`${file.name}-${idx}`}
                      className="flex items-center justify-between rounded-lg border border-neutral-800 bg-slate-950/70 px-3 py-2 text-xs text-slate-200"
                    >
                      <div className="flex items-center gap-2.5 truncate">
                        <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                        <span className="truncate font-medium">{file.name}</span>
                        <span className="text-[10px] text-neutral-400 flex-shrink-0">
                          ({formatFileSize(file.size)})
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeFile(idx);
                        }}
                        className="rounded p-1 text-neutral-400 hover:bg-neutral-800 hover:text-rose-400 transition-colors"
                        title="Remove resume"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-6 flex-grow flex items-center justify-center text-xs text-neutral-500 italic">
                  No resumes in queue yet. Upload files to begin.
                </div>
              )}
            </div>
          </div>

          {/* Advanced Weights Tuning (Optional) */}
          <div className="rounded-xl border border-neutral-800 bg-slate-900/40 p-4">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center justify-between w-full text-xs text-neutral-400 hover:text-neutral-200 font-medium transition-colors"
            >
              <span className="flex items-center gap-2">
                <Sliders className="w-3.5 h-3.5 text-sky-400" />
                Scoring Formula Weights (Default: 65% Text Similarity / 35% Skill Match)
              </span>
              {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showAdvanced && (
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-6 pt-4 border-t border-neutral-800 text-xs">
                <div>
                  <div className="flex justify-between text-neutral-300 mb-1.5 font-medium">
                    <span>Text Similarity Weight:</span>
                    <span className="text-blue-400 font-mono">{(weightTextSim * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={weightTextSim}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      setWeightTextSim(val);
                      setWeightSkillMatch(parseFloat((1 - val).toFixed(2)));
                    }}
                    className="w-full accent-blue-500"
                  />
                </div>
                <div>
                  <div className="flex justify-between text-neutral-300 mb-1.5 font-medium">
                    <span>Skill Match Weight:</span>
                    <span className="text-indigo-400 font-mono">{(weightSkillMatch * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={weightSkillMatch}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      setWeightSkillMatch(val);
                      setWeightTextSim(parseFloat((1 - val).toFixed(2)));
                    }}
                    className="w-full accent-indigo-500"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Error Message Alert */}
          {error && (
            <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs sm:text-sm text-rose-300 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div className="flex-grow">{error}</div>
              <button
                type="button"
                onClick={() => setError(null)}
                className="text-rose-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Submit Action Button */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
            <p className="text-xs text-neutral-400">
              Deterministic pure-Python evaluation &bull; Windows Application Control safe
            </p>
            <button
              type="submit"
              disabled={isLoading || files.length === 0 || jobDescription.trim().length < 30}
              className={`inline-flex items-center justify-center gap-2.5 rounded-xl px-8 py-3.5 text-sm font-semibold text-white shadow-xl transition-all ${
                isLoading || files.length === 0 || jobDescription.trim().length < 30
                  ? "bg-neutral-800 text-neutral-500 cursor-not-allowed opacity-60"
                  : "bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-500 hover:from-blue-500 hover:to-indigo-500 shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5 cursor-pointer"
              }`}
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>{loadingStage || "Screening Resumes..."}</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-white" />
                  <span>Screen &amp; Rank {files.length > 0 ? `(${files.length} Candidates)` : "Resumes"}</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Results Section */}
        {results && (
          <ErrorBoundary fallbackTitle="An error occurred while displaying screening results" onReset={() => setResults(null)}>
            <div ref={resultsRef} className="mt-16 pt-12 border-t border-neutral-800 space-y-8">
              {/* Results Header & Summary Stats */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-1">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Screening Complete &bull; {results.job_title || "Screening Evaluation"}
                  </div>
                  <h3 className="text-2xl font-bold text-white">Candidate Leaderboard &amp; Ranking</h3>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={handleDownloadCsv}
                    disabled={isExporting}
                    className="inline-flex items-center gap-2 rounded-xl border border-neutral-700 bg-neutral-900/80 hover:bg-neutral-800 px-4 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-sm transition-colors cursor-pointer"
                  >
                    <Download className="w-4 h-4 text-blue-400" />
                    <span>{isExporting ? "Exporting..." : "Download CSV Report"}</span>
                  </button>
                  <a
                    href={getStreamlitCandidatesUrl(results.screening_id)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-xl bg-blue-600/20 border border-blue-500/40 hover:bg-blue-600/30 px-4 py-2.5 text-xs sm:text-sm font-semibold text-blue-300 transition-colors"
                  >
                    <span>Open Full ATS View</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>

              {/* Quick Metrics Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="rounded-xl border border-neutral-800 bg-slate-900/50 p-4">
                  <span className="text-xs text-neutral-400">Total Applicants</span>
                  <p className="mt-1 text-2xl font-bold text-white">
                    {results.summary?.total_candidates ?? results.candidates_count ?? (results.results?.length || 0)}
                  </p>
                  <span className="text-[11px] text-emerald-400">
                    {results.summary?.successful_screened ?? results.results?.filter((c) => c.success)?.length ?? 0} parsed successfully
                  </span>
                </div>
                <div className="rounded-xl border border-neutral-800 bg-slate-900/50 p-4">
                  <span className="text-xs text-neutral-400">Top Candidate</span>
                  <p className="mt-1 text-lg font-bold text-white truncate" title={results.summary?.top_candidate || ""}>
                    {results.summary?.top_candidate || results.results?.[0]?.name || results.results?.[0]?.filename || "N/A"}
                  </p>
                  <span className="text-[11px] text-sky-400">Rank #1 Applicant</span>
                </div>
                <div className="rounded-xl border border-neutral-800 bg-slate-900/50 p-4">
                  <span className="text-xs text-neutral-400">Highest Score</span>
                  <p className="mt-1 text-2xl font-bold text-emerald-400">
                    {results.summary?.top_score ?? results.results?.[0]?.overall_score ?? 0}%
                  </p>
                  <span className="text-[11px] text-neutral-400">Leading composite match</span>
                </div>
                <div className="rounded-xl border border-neutral-800 bg-slate-900/50 p-4">
                  <span className="text-xs text-neutral-400">Average Score</span>
                  <p className="mt-1 text-2xl font-bold text-blue-400">
                    {results.summary?.average_score ?? 0}%
                  </p>
                  <span className="text-[11px] text-neutral-400">Across active cohort</span>
                </div>
              </div>

              {/* Candidate Cards Leaderboard */}
              <div className="space-y-4">
                {(results.results || []).map((candidate: CandidateResult, idx: number) => {
                  const badge = getScoreBadge(candidate.overall_score ?? 0, !!candidate.success);
                  const isExpanded = expandedCandidate === candidate.candidate_id;
                  const rankNum = candidate.rank ?? idx + 1;
                  const matchedList = candidate.matched_skills || [];
                  const missingList = candidate.missing_skills || [];

                  return (
                    <div
                      key={candidate.candidate_id || `candidate-${idx}`}
                      className="rounded-2xl border border-neutral-800 bg-slate-900/70 p-5 sm:p-6 transition-all hover:border-neutral-700 shadow-lg"
                    >
                      {/* Main Row */}
                      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                        {/* Left: Rank & Candidate Identity */}
                        <div className="flex items-start gap-4">
                          <div
                            className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl text-sm ${getMedalColor(
                              rankNum
                            )}`}
                          >
                            #{rankNum}
                          </div>
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-2.5">
                              <h4 className="text-base sm:text-lg font-bold text-white">
                                {candidate.name || candidate.filename}
                              </h4>
                              <span
                                className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${badge.color}`}
                              >
                                {badge.label}
                              </span>
                            </div>
                            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-neutral-400">
                              <span className="flex items-center gap-1">
                                <FileText className="w-3.5 h-3.5 text-neutral-500" />
                                {candidate.filename}
                              </span>
                              {candidate.emails && candidate.emails.length > 0 && (
                                <span>{candidate.emails[0]}</span>
                              )}
                              {candidate.phones && candidate.phones.length > 0 && (
                                <span>{candidate.phones[0]}</span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Right: Scores & Actions */}
                        <div className="flex flex-wrap items-center gap-6 lg:justify-end">
                          {/* Overall Score */}
                          <div className="text-right">
                            <div className="text-2xl sm:text-3xl font-black text-white">
                              {candidate.overall_score ?? 0}
                              <span className="text-sm font-normal text-neutral-400">%</span>
                            </div>
                            <span className="text-[11px] text-neutral-400">Composite Score</span>
                          </div>

                          {/* Breakdown Pills */}
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="rounded-lg bg-slate-950/80 px-2.5 py-1.5 border border-neutral-800">
                              <span className="text-neutral-400 block text-[10px]">Text Similarity</span>
                              <span className="font-semibold text-blue-400">
                                {candidate.text_similarity_score ?? 0}%
                              </span>
                            </div>
                            <div className="rounded-lg bg-slate-950/80 px-2.5 py-1.5 border border-neutral-800">
                              <span className="text-neutral-400 block text-[10px]">Skill Match</span>
                              <span className="font-semibold text-indigo-400">
                                {candidate.skill_match_score ?? 0}%
                              </span>
                            </div>
                          </div>

                          {/* Expand / Collapse Evidence Button */}
                          <button
                            type="button"
                            onClick={() => setExpandedCandidate(isExpanded ? null : candidate.candidate_id)}
                            className="rounded-lg border border-neutral-700 bg-neutral-800/80 hover:bg-neutral-800 px-3 py-2 text-xs font-semibold text-neutral-200 transition-colors flex items-center gap-1.5 cursor-pointer"
                          >
                            <span>{isExpanded ? "Hide Details" : "View Details"}</span>
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>
                        </div>
                      </div>

                      {/* Matched & Missing Skills Bar */}
                      <div className="mt-4 pt-4 border-t border-neutral-800/80 flex flex-col sm:flex-row gap-4 text-xs">
                        {/* Matched */}
                        <div className="flex-1">
                          <span className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider block mb-1.5">
                            Matched Skills ({matchedList.length})
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {matchedList.length > 0 ? (
                              matchedList.map((skill) => (
                                <span
                                  key={skill}
                                  className="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 border border-emerald-500/25 px-2 py-0.5 text-[11px] text-emerald-300 font-medium"
                                >
                                  <Check className="w-3 h-3 text-emerald-400" />
                                  {skill}
                                </span>
                              ))
                            ) : (
                              <span className="text-neutral-500 italic text-[11px]">No skill matches detected</span>
                            )}
                          </div>
                        </div>

                        {/* Missing */}
                        <div className="flex-1">
                          <span className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider block mb-1.5">
                            Missing Skills ({missingList.length})
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {missingList.length > 0 ? (
                              missingList.map((skill) => (
                                <span
                                  key={skill}
                                  className="inline-flex items-center gap-1 rounded-md bg-rose-500/10 border border-rose-500/25 px-2 py-0.5 text-[11px] text-rose-300 font-medium"
                                >
                                  <X className="w-3 h-3 text-rose-400" />
                                  {skill}
                                </span>
                              ))
                            ) : (
                              <span className="text-emerald-400 text-[11px]">100% Skill Coverage</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Collapsible Deep-Dive Dossier */}
                      {isExpanded && (
                        <div className="mt-5 pt-5 border-t border-neutral-800 space-y-4 text-xs">
                          {/* Score explanation */}
                          <div className="rounded-xl bg-slate-950/80 p-3.5 border border-neutral-800/80 text-neutral-300 leading-relaxed">
                            <span className="font-semibold text-white block mb-1">Mathematical Scoring Formula:</span>
                            {candidate.score_explanation || "No explanation available."}
                          </div>

                          {/* Evidence Quotes */}
                          {candidate.skill_evidence && Object.keys(candidate.skill_evidence).length > 0 && (
                            <div>
                              <span className="font-semibold text-white block mb-2">
                                Contextual Skill Evidence Quotes ({candidate.evidence_coverage_score ?? 0}% Coverage):
                              </span>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {Object.entries(candidate.skill_evidence).map(([skill, evidence]) => {
                                  const snippets = extractSkillSnippets(evidence);
                                  const tier = extractSkillTier(evidence);
                                  if (!snippets || snippets.length === 0) return null;
                                  return (
                                    <div
                                      key={skill}
                                      className="rounded-lg border border-neutral-800 bg-slate-950/60 p-2.5"
                                    >
                                      <div className="flex items-center justify-between mb-1 gap-2">
                                        <span className="text-blue-400 font-semibold">{skill}:</span>
                                        {tier && (
                                          <span className="text-[10px] text-neutral-400 capitalize bg-neutral-800/80 px-1.5 py-0.5 rounded border border-neutral-700/50">
                                            {tier.replace(/_/g, " ")}
                                          </span>
                                        )}
                                      </div>
                                      <ul className="list-disc list-inside text-neutral-300 space-y-0.5">
                                        {snippets.slice(0, 2).map((q, idx) => (
                                          <li key={idx} className="truncate" title={q}>
                                            &ldquo;{q}&rdquo;
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}

                          {/* Education & Experience Evidence */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {candidate.education_evidence && candidate.education_evidence.length > 0 && (
                              <div className="rounded-xl border border-neutral-800 bg-slate-950/60 p-3">
                                <span className="text-white font-semibold flex items-center gap-1.5 mb-2">
                                  <GraduationCap className="w-4 h-4 text-sky-400" />
                                  Education Snippets
                                </span>
                                <ul className="text-neutral-300 space-y-1">
                                  {candidate.education_evidence.map((edu, idx) => (
                                    <li key={idx}>&bull; {edu}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {candidate.experience_evidence && candidate.experience_evidence.length > 0 && (
                              <div className="rounded-xl border border-neutral-800 bg-slate-950/60 p-3">
                                <span className="text-white font-semibold flex items-center gap-1.5 mb-2">
                                  <Clock className="w-4 h-4 text-emerald-400" />
                                  Experience Snippets
                                </span>
                                <ul className="text-neutral-300 space-y-1">
                                  {candidate.experience_evidence.map((exp, idx) => (
                                    <li key={idx}>&bull; {exp}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>

                          {/* Warnings if any */}
                          {candidate.warning && (
                            <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 p-2.5 text-amber-300 text-xs flex items-center gap-2">
                              <AlertCircle className="w-4 h-4 flex-shrink-0" />
                              <span>{candidate.warning}</span>
                            </div>
                          )}
                          {candidate.error && (
                            <div className="rounded-lg bg-rose-500/10 border border-rose-500/30 p-2.5 text-rose-300 text-xs flex items-center gap-2">
                              <AlertCircle className="w-4 h-4 flex-shrink-0" />
                              <span>{candidate.error}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </ErrorBoundary>
        )}
      </div>
    </section>
  );
}
