"""
Requirement Extractor Module
Extracts skills, education criteria, and requirements from Job Descriptions and Resumes.
Uses word boundaries, regexes, canonical skill taxonomies, and section analysis
to prevent false positive matches and distinguish skill mentions from demonstrable evidence.
"""

import re
from typing import Dict, List, Set, Tuple, Optional, Any
from config import SKILL_TAXONOMY, ALIAS_TO_SKILL, EDUCATION_KEYWORDS, EXPERIENCE_KEYWORDS


# Technical terms requiring special punctuation boundaries
SPECIAL_SYMBOL_SKILLS = {"c++", "c#", ".net"}

# Header regexes for Job Description sections
REQUIRED_HEADER_PATTERN = re.compile(
    r"^(?:#{1,4}\s*)?(?:\*\*|[•\-\*]\s*)?"
    r"(?:required(?:\s+qualifications|\s+skills|\s+experience|\s+requirements)?"
    r"|minimum(?:\s+qualifications|\s+requirements)?"
    r"|must[\s\-]have(?:\s+skills|\s+qualifications)?"
    r"|core(?:\s+requirements|\s+skills|\s+competencies)?"
    r"|basic\s+qualifications"
    r"|what\s+you(?:'ll|\s+will)?\s+need"
    r"|what\s+you\s+bring"
    r"|key\s+requirements"
    r"|requirements"
    r"|responsibilities)"
    r"\s*[:\-]?\s*(?:\*\*)?$",
    re.IGNORECASE
)

PREFERRED_HEADER_PATTERN = re.compile(
    r"^(?:#{1,4}\s*)?(?:\*\*|[•\-\*]\s*)?"
    r"(?:preferred(?:\s+qualifications|\s+skills|\s+experience|\s+requirements)?"
    r"|nice[\s\-]to[\s\-]have(?:\s+skills)?"
    r"|good[\s\-]to[\s\-]have(?:\s+skills)?"
    r"|bonus(?:\s+skills|\s+points)?"
    r"|plus(?:es)?"
    r"|desired(?:\s+qualifications|\s+skills)?"
    r"|optional(?:\s+qualifications)?)"
    r"\s*[:\-]?\s*(?:\*\*)?$",
    re.IGNORECASE
)

# Resume structural section header patterns
RESUME_EXPERIENCE_HEADER = re.compile(
    r"^(?:#{1,4}\s*)?(?:\*\*)?(?:work\s+experience|professional\s+experience|employment\s+history|experience|career\s+history|work\s+history)\s*[:\-]?\s*(?:\*\*)?$",
    re.IGNORECASE
)

RESUME_PROJECTS_HEADER = re.compile(
    r"^(?:#{1,4}\s*)?(?:\*\*)?(?:projects|personal\s+projects|academic\s+projects|technical\s+projects|key\s+projects)\s*[:\-]?\s*(?:\*\*)?$",
    re.IGNORECASE
)

RESUME_SKILLS_HEADER = re.compile(
    r"^(?:#{1,4}\s*)?(?:\*\*)?(?:technical\s+skills|core\s+competencies|skills\s*(?:&|and)\s*technologies|skills|technologies|tools\s*(?:&|and)\s*technologies)\s*[:\-]?\s*(?:\*\*)?$",
    re.IGNORECASE
)

RESUME_EDUCATION_HEADER = re.compile(
    r"^(?:#{1,4}\s*)?(?:\*\*)?(?:education|academic\s+background|degrees|certifications)\s*[:\-]?\s*(?:\*\*)?$",
    re.IGNORECASE
)

# Metric / Achievement indicator regex
ACHIEVEMENT_INDICATOR_PATTERN = re.compile(
    r"(?:\b\d+(?:\.\d+)?%\b|\$\s*\d+|\b\d+\+?\s*(?:users|clients|customers|requests|queries|tps|ms|seconds|million|billion|gb|tb)\b|"
    r"\b(?:reduced|increased|improved|boosted|optimized|accelerated|automated|scaled|delivered|achieved|saved|streamlined|spearheaded)\b)",
    re.IGNORECASE
)


def normalize_text_for_search(text: str) -> str:
    """Normalize text spacing and lowercase while preserving symbols like C++, C#, .NET."""
    text = text.replace("\r", " ").replace("\n", " ")
    return " " + " ".join(text.split()) + " "


def match_variant_in_text(variant: str, canonical: str, text: str) -> bool:
    """
    Check if a specific skill variant appears in text with strict boundary and context awareness.
    Prevents false positive matches for ambiguous words (e.g. 'go', 'r', 'c').
    """
    v_lower = variant.lower()

    # 1. Special symbols (C++, C#, .NET)
    if v_lower in SPECIAL_SYMBOL_SKILLS:
        v_escaped = re.escape(variant)
        pattern = rf"(?:^|[\s,;:\(\)\[\]/]){v_escaped}(?:[\s,;:\(\)\[\]/.]|$)"
        return bool(re.search(pattern, text, re.IGNORECASE))

    # 2. Go programming language
    if canonical == "Go":
        if v_lower in ("golang", "go language"):
            return bool(re.search(rf"\b{re.escape(v_lower)}\b", text, re.IGNORECASE))
        if v_lower == "go":
            # Match 'Go' only when uppercase or accompanied by technical context/lists
            # Never match generic lowercase 'go' ("go to office", "will go", "let's go")
            patterns = [
                r"\b(?:go\s+(?:programming|lang|language|developer|engineer|code|sdk))\b",
                r"\b(?:golang|python|java|rust|c\+\+|c#|kotlin|ruby|php|sql|docker|k8s|kubernetes|node\.js|typescript|react)[\s,/|]+Go\b",
                r"\bGo[\s,/|]+(?:golang|python|java|rust|c\+\+|c#|kotlin|ruby|php|sql|docker|k8s|kubernetes|node\.js|typescript|react)\b",
                r"(?:skills|languages|technologies)\s*[:\-][^\n]*\bGo\b",
            ]
            for pat in patterns:
                if re.search(pat, text, re.IGNORECASE if "skills" in pat or "programming" in pat else 0):
                    return True
            # Also accept standalone uppercase 'Go' in bulleted list items (e.g. "- Go, Python, SQL")
            for line in text.split("\n"):
                line_str = line.strip()
                if line_str.startswith(("-", "*", "•")) and re.search(r"\bGo\b", line_str) and not re.search(r"\bto\b|\bthrough\b|\bahead\b", line_str, re.IGNORECASE):
                    # Check if line contains other tech words or is short
                    if len(line_str) < 80:
                        return True
            return False

    # 3. R programming language
    if canonical == "R":
        if v_lower in ("r programming", "r language"):
            return bool(re.search(rf"\b{re.escape(v_lower)}\b", text, re.IGNORECASE))
        if v_lower == "r":
            # Match 'R' only in explicit programming context
            patterns = [
                r"\b(?:r\s+programming|r\s+language|r\s+script(?:s|ing)?|r\s+package[s]?|r\s+markdown)\b",
                r"\b(?:python|sql|sas|matlab|spss|stata|tableau)[\s,/]+[rR]\b",
                r"\b[rR][\s,/]+(?:python|sql|sas|matlab|spss|stata|tableau)\b",
                r"(?:skills|languages|technologies)\s*[:\-][^\n]*\b[rR]\b"
            ]
            for pat in patterns:
                if re.search(pat, text, re.IGNORECASE):
                    return True
            return False

    # 4. Standard word boundary matching
    v_escaped = re.escape(variant)
    pattern = rf"\b{v_escaped}\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def extract_skills(text: str) -> List[str]:
    """
    Extract canonical skills from text using robust boundary-aware pattern matching.
    Prevents false substring and homonym matches.
    """
    if not text or not text.strip():
        return []

    found_skills: Set[str] = set()

    for canonical, aliases in SKILL_TAXONOMY.items():
        all_variants = [canonical] + aliases
        for variant in all_variants:
            if match_variant_in_text(variant, canonical, text):
                found_skills.add(canonical)
                break

    return sorted(list(found_skills))


def is_section_header(line: str) -> Tuple[bool, Optional[str]]:
    """
    Determine if a line is an explicit job description section header.
    Returns (is_header, section_type) where section_type is 'required', 'preferred', or None.
    Rejects body sentences that casually contain 'prefer' or 'require'.
    """
    line_clean = line.strip()
    if not line_clean or len(line_clean) > 80:
        return False, None

    # Sentence ending in period is almost never a header
    if line_clean.endswith(".") and not line_clean.lower().endswith("etc."):
        return False, None

    if PREFERRED_HEADER_PATTERN.match(line_clean):
        return True, "preferred"

    if REQUIRED_HEADER_PATTERN.match(line_clean):
        return True, "required"

    return False, None


def extract_job_sections(job_text: str) -> Dict[str, Any]:
    """
    Parse a job description into structured sections:
    - required: Required skills / qualifications / responsibilities
    - preferred: Nice to have / preferred / bonus qualifications
    - general: General job overview / other content
    - has_explicit_sections: True if explicit required/preferred headers were detected
    - section_source: 'explicit' | 'inferred' | 'empty'
    """
    if not job_text or not job_text.strip():
        return {
            "required": "",
            "preferred": "",
            "general": "",
            "has_explicit_sections": False,
            "section_source": "empty"
        }

    sections = {
        "required": "",
        "preferred": "",
        "general": ""
    }

    lines = job_text.split("\n")
    current_sec = "general"
    explicit_headers_found = 0

    for line in lines:
        is_header, sec_type = is_section_header(line)
        if is_header and sec_type:
            current_sec = sec_type
            explicit_headers_found += 1
            continue

        if current_sec == "preferred":
            sections["preferred"] += line + "\n"
        elif current_sec == "required":
            sections["required"] += line + "\n"
        else:
            sections["general"] += line + "\n"

    has_explicit = explicit_headers_found > 0

    return {
        "required": sections["required"],
        "preferred": sections["preferred"],
        "general": sections["general"],
        "has_explicit_sections": has_explicit,
        "section_source": "explicit" if has_explicit else "inferred"
    }


def extract_job_requirements(job_description: str) -> Dict[str, Any]:
    """
    Analyze job description to extract required vs preferred skills,
    education requirements, and experience requirements.
    Transparently falls back to treating skills as required if no preferred section exists.
    """
    sections = extract_job_sections(job_description)

    # All skills present anywhere in the job description
    all_skills = extract_skills(job_description)

    preferred_text = sections.get("preferred", "")
    required_text = sections.get("required", "")
    has_explicit = sections.get("has_explicit_sections", False)

    preferred_skills = extract_skills(preferred_text) if preferred_text else []

    if preferred_skills:
        # If preferred skills are identified from a dedicated section,
        # required skills are all remaining detected skills
        required_skills = [s for s in all_skills if s not in preferred_skills]
    else:
        # Transparent fallback: all skills detected in job description are required
        required_skills = all_skills
        preferred_skills = []

    # Extract education mentions
    education_mentions = []
    for line in job_description.split("\n"):
        line_clean = line.strip()
        if any(ek in line_clean.lower() for ek in EDUCATION_KEYWORDS) and len(line_clean) < 200:
            education_mentions.append(line_clean)

    # Extract experience mentions
    experience_mentions = []
    for line in job_description.split("\n"):
        line_clean = line.strip()
        if any(ek in line_clean.lower() for ek in EXPERIENCE_KEYWORDS) and len(line_clean) < 200:
            experience_mentions.append(line_clean)

    return {
        "all_skills": all_skills,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "education_requirements": education_mentions[:5],
        "experience_requirements": experience_mentions[:5],
        "total_skills_count": len(all_skills),
        "has_explicit_sections": has_explicit,
        "section_source": sections.get("section_source", "inferred")
    }


def extract_job_title(job_description: str) -> str:
    """
    Extract or infer a concise job title from the job description text.
    Handles explicit labels (Job Title:, Position:, Role:), recognized role patterns,
    neutral fallback ('Custom Job Description') when text is present,
    or 'Not Specified' when empty.
    """
    if not job_description or not job_description.strip():
        return "Not Specified"

    lines = [line.strip() for line in job_description.split("\n") if line.strip()]
    if not lines:
        return "Not Specified"

    # 1. Check for explicit prefix lines in the first 10 lines
    prefix_patterns = [
        r"^(?:job\s+title|position(?:\s+title)?|role|title)\s*[:\-]\s*(.+)$",
    ]
    for line in lines[:10]:
        for pat in prefix_patterns:
            m = re.match(pat, line, re.IGNORECASE)
            if m:
                extracted = m.group(1).strip()
                extracted = re.sub(r"[\s\:\-]+$", "", extracted)
                if extracted and len(extracted) <= 60:
                    return extracted

    # 2. Check for exact or close matches in the first non-empty line (if short and header-like)
    first_line = lines[0]
    if len(first_line) <= 60 and not any(kw in first_line.lower() for kw in ["description", "overview", "summary", "about us", "we are looking", "requirements"]):
        known_header_titles = [
            "Java Full Stack Developer",
            "Java Developer",
            "Python Developer",
            "Frontend Developer",
            "Front-End Developer",
            "Backend Developer",
            "Back-End Developer",
            "Full Stack Developer",
            "Data Analyst",
            "Data Scientist",
            "Cybersecurity Analyst",
            "Software Engineer",
            "DevOps Engineer",
            "Machine Learning Engineer",
            "QA Engineer",
            "Cloud Architect"
        ]
        for known in known_header_titles:
            if re.search(rf"\b{re.escape(known)}\b", first_line, re.IGNORECASE):
                return known

    # 3. Pattern match across the entire text for recognized roles
    text_lower = job_description.lower()
    role_checks = [
        ("Java Full Stack Developer", ["java full stack", "java full-stack"]),
        ("Python Developer", ["python developer", "python engineer", "python software engineer"]),
        ("Java Developer", ["java developer", "java engineer", "java software engineer"]),
        ("Frontend Developer", ["frontend developer", "front-end developer", "frontend engineer", "front-end engineer", "ui engineer"]),
        ("Backend Developer", ["backend developer", "back-end developer", "backend engineer"]),
        ("Data Analyst", ["data analyst", "senior data analyst", "junior data analyst", "bi analyst"]),
        ("Data Scientist", ["data scientist", "machine learning scientist"]),
        ("Cybersecurity Analyst", ["cybersecurity analyst", "cyber security analyst", "security analyst", "information security analyst"]),
        ("DevOps Engineer", ["devops engineer", "devops specialist", "site reliability engineer", "sre"]),
        ("Machine Learning Engineer", ["machine learning engineer", "ml engineer", "ai engineer"]),
        ("Software Engineer", ["software engineer", "software development engineer", "sde", "software programmer"]),
    ]

    for title, keywords in role_checks:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                return title

    # 4. Fallback if text is provided but no specific title matched
    return "Custom Job Description"


def parse_resume_sections(text: str) -> Dict[str, List[str]]:
    """
    Segment resume into logical sections (experience, projects, skills, education, general).
    Used to locate contextual evidence for detected skills.
    """
    sections = {
        "experience": [],
        "projects": [],
        "skills": [],
        "education": [],
        "general": []
    }

    current_sec = "general"
    for line in text.split("\n"):
        line_clean = line.strip()
        if not line_clean:
            continue

        # Check section boundaries
        if len(line_clean) < 60:
            if RESUME_EXPERIENCE_HEADER.match(line_clean):
                current_sec = "experience"
                continue
            elif RESUME_PROJECTS_HEADER.match(line_clean):
                current_sec = "projects"
                continue
            elif RESUME_SKILLS_HEADER.match(line_clean):
                current_sec = "skills"
                continue
            elif RESUME_EDUCATION_HEADER.match(line_clean):
                current_sec = "education"
                continue

        sections[current_sec].append(line_clean)

    return sections


def extract_skill_evidence(raw_text: str, candidate_skills: List[str]) -> Dict[str, Any]:
    """
    Explainable evidence layer: distinguishes skill mentions in bare lists vs
    demonstrated work experience, project work, and concrete achievements.
    Returns:
    - evidence_by_skill: Dict[skill_name, Dict with tier, snippets, and achievement flag]
    - evidence_coverage_ratio: float in [0.0, 1.0]
    - bare_mentions_count: int
    - warnings: List[str]
    """
    if not raw_text or not candidate_skills:
        return {
            "evidence_by_skill": {},
            "evidence_coverage_ratio": 0.0,
            "bare_mentions_count": 0,
            "warnings": []
        }

    sections = parse_resume_sections(raw_text)
    evidence_by_skill: Dict[str, Dict[str, Any]] = {}
    skills_with_demonstrated_evidence = 0
    bare_mentions = []

    for skill in candidate_skills:
        variants = [skill] + SKILL_TAXONOMY.get(skill, [])
        skill_evidence_records = []

        # Check sections in priority order
        for sec_name, lines in sections.items():
            for line in lines:
                has_match = any(match_variant_in_text(v, skill, line) for v in variants)
                if has_match:
                    has_achievement = bool(ACHIEVEMENT_INDICATOR_PATTERN.search(line))
                    category = "achievement" if has_achievement and sec_name in ("experience", "projects") else (
                        "work_experience" if sec_name == "experience" else (
                            "project" if sec_name == "projects" else (
                                "skills_list" if sec_name == "skills" else "mention_only"
                            )
                        )
                    )
                    skill_evidence_records.append({
                        "section": sec_name,
                        "category": category,
                        "has_achievement": has_achievement,
                        "snippet": line[:180]
                    })

        # Determine dominant evidence tier
        if any(r["category"] == "achievement" for r in skill_evidence_records):
            top_tier = "achievement"
        elif any(r["category"] == "work_experience" for r in skill_evidence_records):
            top_tier = "work_experience"
        elif any(r["category"] == "project" for r in skill_evidence_records):
            top_tier = "project"
        elif any(r["category"] == "skills_list" for r in skill_evidence_records):
            top_tier = "skills_list"
        else:
            top_tier = "mention_only"

        if top_tier in ("achievement", "work_experience", "project"):
            skills_with_demonstrated_evidence += 1
        elif top_tier in ("skills_list", "mention_only"):
            bare_mentions.append(skill)

        evidence_by_skill[skill] = {
            "tier": top_tier,
            "is_demonstrated": top_tier in ("achievement", "work_experience", "project"),
            "snippets": [r["snippet"] for r in skill_evidence_records[:3]],
            "records": skill_evidence_records[:5]
        }

    coverage_ratio = round(skills_with_demonstrated_evidence / len(candidate_skills), 3) if candidate_skills else 0.0

    warnings = []
    if bare_mentions:
        warnings.append(
            f"{len(bare_mentions)} skill(s) detected only as bare keyword mentions without contextual work or project evidence: {', '.join(bare_mentions[:4])}{'...' if len(bare_mentions) > 4 else ''}."
        )

    return {
        "evidence_by_skill": evidence_by_skill,
        "evidence_coverage_ratio": coverage_ratio,
        "bare_mentions_count": len(bare_mentions),
        "warnings": warnings
    }
