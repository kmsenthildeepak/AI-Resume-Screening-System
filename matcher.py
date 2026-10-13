
"""
Matcher Module
Pure-Python TF-IDF, cosine similarity, and skill-overlap scoring.

Avoids scikit-learn and NumPy so the matcher does not depend on
their compiled extensions. Keeps the existing result structure.
"""

from typing import List, Dict, Any
import math
import re
from collections import Counter

from config import (
    DEFAULT_WEIGHT_TEXT_SIMILARITY,
    DEFAULT_WEIGHT_SKILL_MATCH,
)
from requirement_extractor import extract_skills, extract_job_requirements


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

    Returns scores between 0.0 and 1.0.
    """
    if not documents:
        return []

    if not query_text or not query_text.strip():
        return [0.0] * len(documents)

    query_terms = make_terms(query_text)
    document_terms = [
        make_terms(document or "") for document in documents
    ]

    # Empty resumes should always receive zero text similarity.
    corpus = [query_terms] + document_terms

    document_frequency = Counter()
    for terms in corpus:
        document_frequency.update(set(terms))

    total_documents = len(corpus)

    def create_vector(terms: List[str]) -> Dict[str, float]:
        if not terms:
            return {}

        counts = Counter(terms)
        total_terms = len(terms)
        vector = {}

        for term, count in counts.items():
            # Linear term frequency with smoothed inverse document frequency
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
) -> Dict[str, Any]:
    """
    Calculate matched and missing skills.
    Required skills carry 80% weight and preferred skills 20%
    when preferred skills are present.
    """

    # Case-insensitive comparison avoids mismatches such as Java vs JAVA.
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

    matched = sorted({
        required_lookup[key] for key in matched_req_keys
    } | {
        preferred_lookup[key] for key in matched_pref_keys
    })

    missing = sorted({
        required_lookup[key] for key in missing_req_keys
    } | {
        preferred_lookup[key] for key in missing_pref_keys
    })

    if not required_lookup and not preferred_lookup:
        return {
            "score": 0.0,
            "matched_skills": matched,
            "missing_skills": missing,
            "has_job_skills": False,
        }

    if preferred_lookup:
        required_score = (
            len(matched_req_keys) / len(required_lookup)
            if required_lookup else 1.0
        )
        preferred_score = (
            len(matched_pref_keys) / len(preferred_lookup)
            if preferred_lookup else 1.0
        )
        score = 0.80 * required_score + 0.20 * preferred_score
    else:
        score = (
            len(matched_req_keys) / len(required_lookup)
            if required_lookup else 0.0
        )

    return {
        "score": max(0.0, min(1.0, score)),
        "matched_skills": matched,
        "missing_skills": missing,
        "has_job_skills": True,
    }


def rank_resumes(
    job_description: str,
    parsed_resumes: List[Dict[str, Any]],
    weight_text_sim: float = DEFAULT_WEIGHT_TEXT_SIMILARITY,
    weight_skill_match: float = DEFAULT_WEIGHT_SKILL_MATCH,
) -> List[Dict[str, Any]]:
    """Rank parsed resumes and return candidate results with evidence."""

    if not parsed_resumes:
        return []

    job_reqs = extract_job_requirements(job_description)
    job_required = job_reqs["required_skills"]
    job_preferred = job_reqs["preferred_skills"]
    has_job_skills = job_reqs["total_skills_count"] > 0

    resume_texts = [
        resume.get("raw_text", "") if resume.get("success") else ""
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
                "matched_skills": [],
                "missing_skills": job_reqs.get("all_skills", []),
                "candidate_skills": [],
                "education_evidence": [],
                "experience_evidence": [],
                "raw_text": "",
                "score_explanation": (
                    "Extraction failed: candidate could not be analyzed."
                ),
            })
            continue

        raw_text = resume.get("raw_text", "")
        candidate_skills = extract_skills(raw_text)

        skill_result = calculate_skill_match_score(
            candidate_skills, job_required, job_preferred
        )

        skill_score = skill_result["score"]
        text_score = text_similarities[index]

        if has_job_skills:
            overall_raw = (
                weight_text_sim * text_score
                + weight_skill_match * skill_score
            )
            explanation = (
                f"Composite score: {weight_text_sim * 100:.0f}% "
                f"Text Similarity ({text_score * 100:.1f}%) + "
                f"{weight_skill_match * 100:.0f}% Skill Overlap "
                f"({skill_score * 100:.1f}%)."
            )
        else:
            overall_raw = text_score
            explanation = (
                f"100% Text Similarity ({text_score * 100:.1f}%). "
                "No standard skills detected in job description "
                "to compute skill overlap."
            )

        results.append({
            "candidate_id": candidate_id,
            "filename": filename,
            "name": resume.get("name"),
            "emails": resume.get("emails", []),
            "phones": resume.get("phones", []),
            "success": True,
            "error": None,
            "warning": resume.get("warning"),
            "overall_score": round(overall_raw * 100, 2),
            "text_similarity_score": round(text_score * 100, 2),
            "skill_match_score": round(skill_score * 100, 2),
            "matched_skills": skill_result["matched_skills"],
            "missing_skills": skill_result["missing_skills"],
            "candidate_skills": candidate_skills,
            "education_evidence": resume.get("education_evidence", []),
            "experience_evidence": resume.get("experience_evidence", []),
            "raw_text": raw_text,
            "score_explanation": explanation,
        })

    results.sort(
        key=lambda result: (
            result["overall_score"],
            result["text_similarity_score"],
            result["candidate_id"],
        ),
        reverse=True,
    )

    for rank, candidate in enumerate(results, start=1):
        candidate["rank"] = rank

    return results
