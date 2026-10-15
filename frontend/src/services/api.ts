/**
 * API Service for interacting with FastAPI AI Resume Screening Backend.
 * Base URL is dynamically resolved via import.meta.env.VITE_API_BASE_URL.
 */

export interface SkillEvidenceRecord {
  section?: string;
  category?: string;
  has_achievement?: boolean;
  snippet?: string;
}

export interface SkillEvidenceItem {
  tier?: string;
  is_demonstrated?: boolean;
  snippets?: string[];
  records?: SkillEvidenceRecord[];
}

export interface CandidateResult {
  candidate_id: string;
  doc_id?: string;
  filename: string;
  name: string | null;
  emails: string[];
  phones: string[];
  success: boolean;
  error: string | null;
  warning: string | null;
  evidence_warnings?: string[];
  overall_score: number;
  text_similarity_score: number;
  skill_match_score: number;
  evidence_coverage_score: number;
  matched_skills: string[];
  missing_skills: string[];
  matched_required_skills?: string[];
  missing_required_skills?: string[];
  matched_preferred_skills?: string[];
  missing_preferred_skills?: string[];
  candidate_skills: string[];
  skill_evidence: Record<string, SkillEvidenceItem | string[] | unknown>;
  education_evidence: string[];
  experience_evidence: string[];
  raw_text?: string;
  score_explanation: string;
  rank: number;
}

/**
 * Safely extract text snippets from diverse skill evidence structures
 * (handles dict with snippets/records as well as plain string arrays).
 */
export function extractSkillSnippets(evidence: unknown): string[] {
  if (!evidence) return [];
  if (Array.isArray(evidence)) {
    return evidence.filter((s): s is string => typeof s === "string");
  }
  if (typeof evidence === "object" && evidence !== null) {
    const item = evidence as SkillEvidenceItem;
    if (Array.isArray(item.snippets)) {
      return item.snippets.filter((s): s is string => typeof s === "string");
    }
    if (Array.isArray(item.records)) {
      return item.records
        .map((r) => r?.snippet)
        .filter((s): s is string => typeof s === "string");
    }
  }
  return [];
}

/**
 * Safely extract evidence tier category (e.g. work_experience, project, skills_list).
 */
export function extractSkillTier(evidence: unknown): string | null {
  if (evidence && typeof evidence === "object" && !Array.isArray(evidence)) {
    const item = evidence as SkillEvidenceItem;
    return typeof item.tier === "string" ? item.tier : null;
  }
  return null;
}

export interface ScreeningSummary {
  total_candidates: number;
  successful_screened: number;
  failed_screened: number;
  top_candidate: string | null;
  top_score: number;
  average_score: number;
}

export interface ScreeningResponse {
  screening_id: string;
  job_title: string;
  job_description: string;
  candidates_count: number;
  summary: ScreeningSummary;
  results: CandidateResult[];
  weights: {
    text_similarity: number;
    skill_match: number;
  };
  timestamp: number;
}

export interface SampleJdResponse {
  sample_job_description: string;
  title: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

const getApiBaseUrl = (): string => {
  // Read VITE_API_BASE_URL, default to localhost:8000 in local dev or empty string for relative proxy
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (typeof envUrl === "string" && envUrl.trim() !== "") {
    return envUrl.replace(/\/+$/, "");
  }
  // Default to localhost:8000 when running in dev mode
  return "http://localhost:8000";
};

export const API_BASE_URL = getApiBaseUrl();

/**
 * Perform a health check against the FastAPI service.
 */
export async function checkApiHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    method: "GET",
  });
  if (!res.ok) {
    throw new Error(`API health check failed with status ${res.status}`);
  }
  return res.json();
}

/**
 * Fetch default sample job description template.
 */
export async function fetchSampleJobDescription(): Promise<SampleJdResponse> {
  const res = await fetch(`${API_BASE_URL}/api/sample-jd`, {
    method: "GET",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch sample job description: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Submit job description and resume files for parsing, matching, and ranking.
 */
export async function screenResumes(
  jobDescription: string,
  files: File[],
  weightTextSim: number = 0.65,
  weightSkillMatch: number = 0.35
): Promise<ScreeningResponse> {
  const formData = new FormData();
  formData.append("job_description", jobDescription);
  formData.append("weight_text_sim", weightTextSim.toString());
  formData.append("weight_skill_match", weightSkillMatch.toString());

  for (const file of files) {
    formData.append("files", file);
  }

  const res = await fetch(`${API_BASE_URL}/api/screen`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    let errorDetail = `Screening failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

/**
 * Retrieve cached screening results by screening_id.
 */
export async function getScreeningResults(screeningId: string): Promise<ScreeningResponse> {
  const res = await fetch(`${API_BASE_URL}/api/screening/${screeningId}`, {
    method: "GET",
  });
  if (!res.ok) {
    throw new Error(`Failed to load screening session: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Get the direct download URL for exporting screening results to CSV.
 */
export function getExportCsvUrl(screeningId: string): string {
  return `${API_BASE_URL}/api/screening/${screeningId}/export`;
}

/**
 * Trigger file download for CSV screening report.
 */
export async function downloadScreeningCsv(screeningId: string): Promise<void> {
  const downloadUrl = getExportCsvUrl(screeningId);
  const res = await fetch(downloadUrl);
  if (!res.ok) {
    throw new Error(`Failed to download CSV report: ${res.statusText}`);
  }

  const blob = await res.blob();
  const blobUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = `screening_report_${screeningId.slice(0, 8)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(blobUrl);
}

/**
 * Resolves the Streamlit ATS URL targeting the Candidates page with an optional screening session ID.
 */
export function getStreamlitCandidatesUrl(sessionId?: string): string {
  const envUrl = import.meta.env.VITE_STREAMLIT_URL;
  const baseUrl = (typeof envUrl === "string" && envUrl.trim() !== "")
    ? envUrl.trim().replace(/\/+$/, "")
    : "http://localhost:8501";

  try {
    const url = new URL(baseUrl);
    url.searchParams.set("page", "Candidates");
    if (sessionId && sessionId.trim() !== "") {
      url.searchParams.set("session_id", sessionId.trim());
    }
    return url.toString();
  } catch {
    const sep = baseUrl.includes("?") ? "&" : "?";
    let target = `${baseUrl}${sep}page=Candidates`;
    if (sessionId && sessionId.trim() !== "") {
      target += `&session_id=${encodeURIComponent(sessionId.trim())}`;
    }
    return target;
  }
}

