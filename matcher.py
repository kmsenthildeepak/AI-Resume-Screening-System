"""
Matcher Module
Pure-Python TF-IDF, cosine similarity, skill-overlap scoring, and explainable candidate ranking.

Avoids scikit-learn and NumPy compiled dependencies for compatibility with Windows Application Control.
Preserves existing output structures while adding explainable evidence and rigorous mathematical scoring.
"""

from typing import List, Dict, Any, Tuple, Optional
import math
import re
from collections import Counter

from config import (
    DEFAULT_WEIGHT_TEXT_SIMILARITY,
    DEFAULT_WEIGHT_SKILL_MATCH,
    DEFAULT_REQUIRED_SKILL_WEIGHT,
    DEFAULT_PREFERRED_SKILL_WEIGHT,
    ALIAS_TO_SKILL,
    SKILL_TAXONOMY,
)
from requirement_extractor import (
    extract_skills,
    extract_job_requirements,
    extract_skill_evidence,
)


# Common English words excluded from text similarity.
STOP_WORDS = set("""
a an the and or but if then else for to of in on at by from with
as is are was were be been being it its this that these those
i we you he she they them our your their my his her who which
what when where how why do does did have has had can could should
would will may might must not no yes into over under about after
before between during through above below up down out off more most
some any all each every other such than too very also only own same
so just both few many much because while although until again
""".split())


def tokenize(text: str) -> List[str]:
    """
    Tokenize text while preserving common technical terms such as
    C++, C#, .NET, Node.js, and CI/CD.
    """
    if not text:
        return []

    text = text.lower()
    pattern = r"\.net|c\+\+|c#|f#|node\.js|ci/cd|[\w]+(?:[.+#/-][\w+#]+)*"
    tokens = re.findall(pattern, text)

    return [
        token for token in tokens
        if token not in STOP_WORDS and len(token) > 1
    ]


def make_terms(text: str) -> List[str]:
    """Tokenize text into feature terms."""
    return tokenize(text)


def compute_cosine_similarity(vec1: Any, vec2: Any) -> float:
    """Compute cosine similarity between sparse dictionaries or sequence/numpy vectors."""
    if vec1 is None or vec2 is None:
        return 0.0

    if isinstance(vec1, dict) and isinstance(vec2, dict):
        if not vec1 or not vec2:
            return 0.0
        dot_product = sum(
            value * vec2.get(term, 0.0)
            for term, value in vec1.items()
        )
        norm1 = math.sqrt(sum(value * value for value in vec1.values()))
        norm2 = math.sqrt(sum(value * value for value in vec2.values()))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, min(1.0, similarity))

    try:
        if len(vec1) == 0 or len(vec2) == 0:
            return 0.0
        dot_product = sum(float(a) * float(b) for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(float(a) * float(a) for a in vec1))
        norm2 = math.sqrt(sum(float(b) * float(b) for b in vec2))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, min(1.0, similarity))
    except Exception:
        return 0.0


def compute_tfidf_similarities(
    query_text: str,
    documents: List[str],
) -> List[float]:
    """
    Calculate TF-IDF cosine similarity between a job description
    and each resume using only Python's standard library.

    Returns scores strictly bounded between 0.0 and 1.0.
    """
    if not documents:
        return []

    if not query_text or not query_text.strip():
        return [0.0] * len(documents)

    query_terms = make_terms(query_text)
    document_terms = [
        make_terms(document or "") for document in documents
    ]

    # Corpus includes query and document terms for shared vocabulary
    corpus = [query_terms] + document_terms

    document_frequency = Counter()
    for terms in corpus:
        document_frequency.update(set(terms))

    total_documents = len(corpus)

    def create_vector(terms: List[str]) -> Dict[str, float]:
        if not terms:
            return {}

        counts = Counter(terms)
        vector = {}

        for term, count in counts.items():
            # Term frequency with smoothed inverse document frequency
            term_frequency = float(count)
            inverse_document_frequency = (
                1.0
                + math.log(
                    (1.0 + total_documents)
                    / (1.0 + document_frequency[term])
                )
            )
            vector[term] = term_frequency * inverse_document_frequency

        return vector

    query_vector = create_vector(query_terms)
    similarities = []

    for terms in document_terms:
        if not terms:
            similarities.append(0.0)
            continue

        document_vector = create_vector(terms)
        similarities.append(
            compute_cosine_similarity(query_vector, document_vector)
        )

    return similarities


def calculate_skill_match_score(
    candidate_skills: List[str],
    job_required_skills: List[str],
    job_preferred_skills: List[str],
    req_weight: float = DEFAULT_REQUIRED_SKILL_WEIGHT,
    pref_weight: float = DEFAULT_PREFERRED_SKILL_WEIGHT,
) -> Dict[str, Any]:
    """
    Calculate matched and missing skills across required and preferred categories.

    Mathematically sound rules:
    - Never awards free credit for an empty skill category.
    - If both required and preferred skills exist:
        score = req_weight * (matched_req / total_req) + pref_weight * (matched_pref / total_pref)
    - If only required skills exist:
        score = matched_req / total_req
    - If only preferred skills exist:
        score = matched_pref / total_pref
    - If no job skills are specified:
        score = 0.0, has_job_skills = False
    - All scores are strictly clamped between 0.0 and 1.0.
    """
    candidate_lookup = {
        skill.strip().casefold(): skill
        for skill in candidate_skills if skill and skill.strip()
    }
    required_lookup = {
        skill.strip().casefold(): skill
        for skill in job_required_skills if skill and skill.strip()
    }
    preferred_lookup = {
        skill.strip().casefold(): skill
        for skill in job_preferred_skills if skill and skill.strip()
    }

    matched_req_keys = set(required_lookup) & set(candidate_lookup)
    missing_req_keys = set(required_lookup) - set(candidate_lookup)
    matched_pref_keys = set(preferred_lookup) & set(candidate_lookup)
    missing_pref_keys = set(preferred_lookup) - set(candidate_lookup)

    matched_req_skills = sorted({required_lookup[k] for k in matched_req_keys})
    missing_req_skills = sorted({required_lookup[k] for k in missing_req_keys})
    matched_pref_skills = sorted({preferred_lookup[k] for k in matched_pref_keys})
    missing_pref_skills = sorted({preferred_lookup[k] for k in missing_pref_keys})

    all_matched = sorted(set(matched_req_skills) | set(matched_pref_skills))
    all_missing = sorted(set(missing_req_skills) | set(missing_pref_skills))

    total_req = len(required_lookup)
    total_pref = len(preferred_lookup)

    if total_req == 0 and total_pref == 0:
        return {
            "score": 0.0,
            "required_score": 0.0,
            "preferred_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "matched_required_skills": [],
            "missing_required_skills": [],
            "matched_preferred_skills": [],
            "missing_preferred_skills": [],
            "has_job_skills": False,
            "total_required_count": 0,
            "total_preferred_count": 0,
        }

    # Normalize category weights if both are present
    if total_req > 0 and total_pref > 0:
        weight_sum = req_weight + pref_weight
        w_req = req_weight / weight_sum if weight_sum > 0 else 0.80
        w_pref = pref_weight / weight_sum if weight_sum > 0 else 0.20

        required_score = len(matched_req_keys) / total_req
        preferred_score = len(matched_pref_keys) / total_pref
        score = (w_req * required_score) + (w_pref * preferred_score)
    elif total_req > 0 and total_pref == 0:
        required_score = len(matched_req_keys) / total_req
        preferred_score = 0.0
        score = required_score
    else:
        # Only preferred skills exist (total_req == 0, total_pref > 0)
        # NEVER award free 1.0 credit for an empty required list!
        required_score = 0.0
        preferred_score = len(matched_pref_keys) / total_pref
        score = preferred_score

    clamped_score = max(0.0, min(1.0, float(score)))

    return {
        "score": clamped_score,
        "required_score": round(required_score, 4),
        "preferred_score": round(preferred_score, 4),
        "matched_skills": all_matched,
        "missing_skills": all_missing,
        "matched_required_skills": matched_req_skills,
        "missing_required_skills": missing_req_skills,
        "matched_preferred_skills": matched_pref_skills,
        "missing_preferred_skills": missing_pref_skills,
        "has_job_skills": True,
        "total_required_count": total_req,
        "total_preferred_count": total_pref,
    }


def validate_and_normalize_weights(
    weight_text_sim: float,
    weight_skill_match: float,
) -> Tuple[float, float, Optional[str]]:
    """
    Validate scoring weights:
    - Must be finite (not NaN, not Inf).
    - Must be non-negative.
    - Cannot both be zero.
    - If valid but sum != 1.0, normalize proportionally.
    - If invalid, fall back safely to defaults with a descriptive warning.
    """
    warning = None

    # Check finite numbers
    try:
        w_text = float(weight_text_sim)
        w_skill = float(weight_skill_match)
        if not math.isfinite(w_text) or not math.isfinite(w_skill):
            raise ValueError("Weights must be finite numbers.")
        if w_text < 0.0 or w_skill < 0.0:
            raise ValueError("Weights must be non-negative.")
        if w_text == 0.0 and w_skill == 0.0:
            raise ValueError("Both weights cannot be zero.")
    except Exception as e:
        warning = f"Invalid weights ({weight_text_sim}, {weight_skill_match}): {str(e)}. Using defaults."
        return DEFAULT_WEIGHT_TEXT_SIMILARITY, DEFAULT_WEIGHT_SKILL_MATCH, warning

    total = w_text + w_skill
    if abs(total - 1.0) > 1e-6:
        w_text = w_text / total
        w_skill = w_skill / total

    return w_text, w_skill, warning


RESUME_SECTION_START = re.compile(
    r"^(?:#{1,4}\s*)?(?:\*\*)?(?:summary|profile|objective|experience|work\s+experience|professional\s+experience|projects|skills|technical\s+skills|education|academic)\b",
    re.IGNORECASE,
)


def strip_pii_for_matching(
    raw_text: str,
    name: Optional[str] = None,
    emails: Optional[List[str]] = None,
    phones: Optional[List[str]] = None,
) -> str:
    """
    Remove candidate personal identifiers (names, emails, phone numbers, profile URLs)
    before vectorization so that personal identities, email lengths, and phone formats
    cannot influence TF-IDF text similarity or composite match scores.

    Safeguards:
    - Never strips tokens matching cataloged skills or technical aliases (e.g. Ruby, Rust, Swift).
    - Preserves ordinary words and domain concepts in project/experience descriptions (e.g. price, mark, grant, art, will).
    - Scopes individual single-word name token removal to the contact preamble header block.
    """
    if not raw_text:
        return ""

    text = raw_text

    # 1. Strip explicit emails and general email patterns globally
    if emails:
        for e in emails:
            if e:
                text = text.replace(e, " ")
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", " ", text)

    # 2. Strip explicit phone numbers and common phone digit patterns globally
    if phones:
        for p in phones:
            if p:
                text = text.replace(p, " ")
    text = re.sub(r"\(?\+?[0-9]{1,4}\)?[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}", " ", text)

    # 3. Strip common profile URLs (LinkedIn, GitHub, personal sites) globally
    text = re.sub(r"https?://\S+|www\.\S+|linkedin\.com\S*|github\.com\S*", " ", text, flags=re.IGNORECASE)

    # 4. If a multi-word full name is provided, strip the full name phrase globally
    clean_name = name.strip() if name else ""
    name_parts = [p.strip() for p in re.split(r"[\s,.-]+", clean_name) if len(p.strip()) > 1]
    if len(name_parts) >= 2:
        text = re.sub(r"\b" + re.escape(clean_name) + r"\b", " ", text, flags=re.IGNORECASE)

    # 5. Split into contact header preamble and substantive body
    lines = text.split("\n")
    header_lines = []
    body_lines = []
    in_header = True

    for i, line in enumerate(lines):
        clean = line.strip()
        if in_header:
            if i >= 1 and (RESUME_SECTION_START.match(clean) or i >= 6):
                in_header = False
                body_lines.append(line)
            else:
                header_lines.append(line)
        else:
            body_lines.append(line)

    header_text = "\n".join(header_lines)
    # Strip individual name parts ONLY from the contact header block (sparing technical skills)
    for part in name_parts:
        lower_part = part.lower()
        if lower_part in ALIAS_TO_SKILL or any(lower_part == s.lower() for s in SKILL_TAXONOMY):
            continue
        header_text = re.sub(r"\b" + re.escape(part) + r"\b", " ", header_text, flags=re.IGNORECASE)

    return header_text + "\n" + "\n".join(body_lines)


def rank_resumes(
    job_description: str,
    parsed_resumes: List[Dict[str, Any]],
    weight_text_sim: float = DEFAULT_WEIGHT_TEXT_SIMILARITY,
    weight_skill_match: float = DEFAULT_WEIGHT_SKILL_MATCH,
) -> List[Dict[str, Any]]:
    """
    Rank parsed resumes and return candidate results with explainable evidence.

    Fairness and Transparency Safeguards:
    - Protected personal attributes (name, email, phone, filename) NEVER influence scores.
    - Failed extractions always receive an overall_score of 0.0 and rank at bottom.
    - Tie-breaking is deterministic: (-overall_score, -text_similarity_score, -skill_match_score, candidate_id).
    - Preserves all evaluated candidates without arbitrary truncation.
    """
    if not parsed_resumes:
        return []

    w_text_sim, w_skill_match, weight_warning = validate_and_normalize_weights(
        weight_text_sim, weight_skill_match
    )

    job_reqs = extract_job_requirements(job_description)
    job_required = job_reqs["required_skills"]
    job_preferred = job_reqs["preferred_skills"]
    has_job_skills = job_reqs["total_skills_count"] > 0

    resume_texts = [
        strip_pii_for_matching(
            resume.get("raw_text", ""),
            name=resume.get("name"),
            emails=resume.get("emails"),
            phones=resume.get("phones"),
        )
        if resume.get("success")
        else ""
        for resume in parsed_resumes
    ]

    text_similarities = compute_tfidf_similarities(
        job_description, resume_texts
    )

    results = []

    for index, resume in enumerate(parsed_resumes):
        filename = resume.get("filename", "unknown")
        candidate_id = f"CAND_{index + 1:03d}_{filename}"

        if not resume.get("success"):
            results.append({
                "candidate_id": candidate_id,
                "filename": filename,
                "name": None,
                "emails": [],
                "phones": [],
                "success": False,
                "error": resume.get("error", "Unknown extraction failure"),
                "warning": resume.get("warning"),
                "overall_score": 0.0,
                "text_similarity_score": 0.0,
                "skill_match_score": 0.0,
                "evidence_coverage_score": 0.0,
                "matched_skills": [],
                "missing_skills": job_reqs.get("all_skills", []),
                "matched_required_skills": [],
                "missing_required_skills": job_required,
                "matched_preferred_skills": [],
                "missing_preferred_skills": job_preferred,
                "candidate_skills": [],
                "skill_evidence": {},
                "education_evidence": [],
                "experience_evidence": [],
                "raw_text": "",
                "score_explanation": "Extraction failed: candidate document could not be parsed.",
            })
            continue

        raw_text = resume.get("raw_text", "")
        candidate_skills = extract_skills(raw_text)

        skill_result = calculate_skill_match_score(
            candidate_skills, job_required, job_preferred
        )

        skill_score = skill_result["score"]
        text_score = text_similarities[index]

        # Extract contextual evidence for candidate skills
        evidence_data = extract_skill_evidence(raw_text, candidate_skills)

        if has_job_skills:
            overall_raw = (
                w_text_sim * text_score
                + w_skill_match * skill_score
            )
            explanation = (
                f"Composite score: {w_text_sim * 100:.0f}% Text Similarity ({text_score * 100:.1f}%) + "
                f"{w_skill_match * 100:.0f}% Skill Overlap ({skill_score * 100:.1f}%)."
            )
        else:
            overall_raw = text_score
            explanation = (
                f"100% Text Similarity ({text_score * 100:.1f}%). "
                "No standard skills detected in job description to compute skill overlap."
            )

        if weight_warning:
            explanation += f" Note: {weight_warning}"

        results.append({
            "candidate_id": candidate_id,
            "filename": filename,
            "name": resume.get("name"),
            "emails": resume.get("emails", []),
            "phones": resume.get("phones", []),
            "success": True,
            "error": None,
            "warning": resume.get("warning"),
            "evidence_warnings": evidence_data.get("warnings", []),
            "overall_score": round(max(0.0, min(100.0, overall_raw * 100)), 2),
            "text_similarity_score": round(max(0.0, min(100.0, text_score * 100)), 2),
            "skill_match_score": round(max(0.0, min(100.0, skill_score * 100)), 2),
            "evidence_coverage_score": round(evidence_data.get("evidence_coverage_ratio", 0.0) * 100, 1),
            "matched_skills": skill_result["matched_skills"],
            "missing_skills": skill_result["missing_skills"],
            "matched_required_skills": skill_result["matched_required_skills"],
            "missing_required_skills": skill_result["missing_required_skills"],
            "matched_preferred_skills": skill_result["matched_preferred_skills"],
            "missing_preferred_skills": skill_result["missing_preferred_skills"],
            "candidate_skills": candidate_skills,
            "skill_evidence": evidence_data.get("evidence_by_skill", {}),
            "education_evidence": resume.get("education_evidence", []),
            "experience_evidence": resume.get("experience_evidence", []),
            "raw_text": raw_text,
            "score_explanation": explanation,
        })

    # Deterministic sorting:
    # 1. Successful candidates outrank failed extractions
    # 2. Highest overall_score
    # 3. Highest text_similarity_score
    # 4. Highest skill_match_score
    # 5. Stable candidate_id
    results.sort(
        key=lambda r: (
            1 if r["success"] else 0,
            r["overall_score"],
            r["text_similarity_score"],
            r["skill_match_score"],
            r["candidate_id"],
        ),
        reverse=True,
    )

    for rank, candidate in enumerate(results, start=1):
        candidate["rank"] = rank

    return results
