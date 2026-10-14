"""
Export Module
Handles safe CSV report generation with formula-injection mitigation,
Unicode support, and structured ranking presentation.
Works independently of pandas using Python's standard csv module.
"""

import csv
import io
from typing import List, Dict, Any


def sanitize_csv_cell(value: Any) -> str:
    """
    Sanitize cell value to prevent CSV / Spreadsheet formula injection.
    Prefixes values starting with '=', '+', '-', '@', '\t', or '\r' with an apostrophe.
    Also handles whitespace padding around dangerous leading characters.
    """
    if value is None:
        return ""
    val_str = str(value)
    if not val_str:
        return ""
    # Check for dangerous spreadsheet leading characters
    stripped = val_str.strip()
    if val_str[0] in ("=", "+", "-", "@", "\t", "\r", "\n") or (stripped and stripped[0] in ("=", "+", "-", "@")):
        return "'" + val_str
    return val_str


def generate_candidates_csv(ranked_candidates: List[Dict[str, Any]]) -> str:
    """
    Generate CSV string from ranked candidate records.
    Returns UTF-8 string with standard headers and sanitized values.
    Appends detailed required vs preferred skills and evidence coverage
    while maintaining full backward compatibility with index-based checks.
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header definition (preserving first 15 columns for backwards compatibility)
    headers = [
        "Rank",
        "Candidate ID",
        "Filename",
        "Candidate Name",
        "Email",
        "Phone",
        "Overall Score (%)",
        "Text Similarity (%)",
        "Skill Match (%)",
        "Matched Skills",
        "Missing Skills",
        "Education Evidence",
        "Experience Evidence",
        "Extraction Status",
        "Error Details",
        "Matched Required Skills",
        "Missing Required Skills",
        "Matched Preferred Skills",
        "Missing Preferred Skills",
        "Evidence Coverage (%)"
    ]
    writer.writerow(headers)

    for cand in ranked_candidates:
        row = [
            sanitize_csv_cell(cand.get("rank", "")),
            sanitize_csv_cell(cand.get("candidate_id", "")),
            sanitize_csv_cell(cand.get("filename", "")),
            sanitize_csv_cell(cand.get("name", "N/A")),
            sanitize_csv_cell(", ".join(cand.get("emails", [])) if cand.get("emails") else "N/A"),
            sanitize_csv_cell(", ".join(cand.get("phones", [])) if cand.get("phones") else "N/A"),
            sanitize_csv_cell(cand.get("overall_score", 0.0)),
            sanitize_csv_cell(cand.get("text_similarity_score", 0.0)),
            sanitize_csv_cell(cand.get("skill_match_score", 0.0)),
            sanitize_csv_cell("; ".join(cand.get("matched_skills", []))),
            sanitize_csv_cell("; ".join(cand.get("missing_skills", []))),
            sanitize_csv_cell(" | ".join(cand.get("education_evidence", []))),
            sanitize_csv_cell(" | ".join(cand.get("experience_evidence", []))),
            sanitize_csv_cell("Success" if cand.get("success") else "Failed"),
            sanitize_csv_cell(cand.get("error", "") if not cand.get("success") else ""),
            sanitize_csv_cell("; ".join(cand.get("matched_required_skills", []))),
            sanitize_csv_cell("; ".join(cand.get("missing_required_skills", []))),
            sanitize_csv_cell("; ".join(cand.get("matched_preferred_skills", []))),
            sanitize_csv_cell("; ".join(cand.get("missing_preferred_skills", []))),
            sanitize_csv_cell(cand.get("evidence_coverage_score", 0.0))
        ]
        writer.writerow(row)

    return output.getvalue()
