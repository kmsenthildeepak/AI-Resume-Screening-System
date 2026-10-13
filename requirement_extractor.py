"""
Requirement Extractor Module
Extracts skills, education criteria, and requirements from Job Descriptions and Resumes.
Uses word boundaries, regexes, and canonical skill taxonomies to prevent false positive matches.
"""

import re
from typing import Dict, List, Set, Tuple, Optional, Any
from config import SKILL_TAXONOMY, ALIAS_TO_SKILL, EDUCATION_KEYWORDS, EXPERIENCE_KEYWORDS


def normalize_text_for_search(text: str) -> str:
    """Normalize text spacing and lowercase while preserving symbols like C++, C#, .NET."""
    text = text.replace("\r", " ").replace("\n", " ")
    return " " + " ".join(text.split()) + " "


def extract_skills(text: str) -> List[str]:
    """
    Extract canonical skills from text using robust regex pattern matching.
    Uses word boundaries and special character boundaries to avoid false substring matches
    (e.g., 'go' inside 'good', 'c' inside 'can', 'r' inside 'read').
    """
    if not text or not text.strip():
        return []

    found_skills: Set[str] = set()

    for canonical, aliases in SKILL_TAXONOMY.items():
        # Test canonical name and all its aliases
        all_variants = [canonical] + aliases
        for variant in all_variants:
            v_escaped = re.escape(variant)
            
            # Special handling for programming languages with symbols or single letters
            if variant.lower() in ["c++", "c#", ".net"]:
                # Needs boundary that handles punctuation
                pattern = rf"(?:^|[\s,;:\(\)\[\]/]){v_escaped}(?:[\s,;:\(\)\[\]/]|$)"
            elif variant.lower() in ["c", "r", "go", "py", "ts", "js", "ml", "dl", "cv", "tf"]:
                # Short acronyms require strict word boundaries and case-awareness or strict context
                # To avoid false positives on 'go' or 'r', we match strictly as whole words
                pattern = rf"\b{v_escaped}\b"
            else:
                pattern = rf"\b{v_escaped}\b"

            if re.search(pattern, text, re.IGNORECASE):
                found_skills.add(canonical)
                break

    return sorted(list(found_skills))


def extract_job_sections(job_text: str) -> Dict[str, str]:
    """
    Parse a job description into structured sections:
    - required: Required skills / qualifications / responsibilities
    - preferred: Nice to have / preferred / bonus qualifications
    """
    sections = {
        "required": "",
        "preferred": "",
        "general": ""
    }

    lines = job_text.split("\n")
    current_sec = "general"

    preferred_keywords = ["preferred", "nice to have", "good to have", "bonus", "plus", "desired", "optional"]
    required_keywords = ["required", "minimum", "must have", "qualifications", "responsibilities", "requirements"]

    for line in lines:
        line_lower = line.strip().lower()
        if any(pk in line_lower for pk in preferred_keywords) and len(line_lower) < 60:
            current_sec = "preferred"
            continue
        elif any(rk in line_lower for rk in required_keywords) and len(line_lower) < 60:
            current_sec = "required"
            continue

        if current_sec == "preferred":
            sections["preferred"] += line + "\n"
        elif current_sec == "required":
            sections["required"] += line + "\n"
        else:
            sections["general"] += line + "\n"

    return sections


def extract_job_requirements(job_description: str) -> Dict[str, Any]:
    """
    Analyze job description to extract required vs preferred skills,
    education requirements, and experience requirements.
    """
    sections = extract_job_sections(job_description)

    # All skills present in the full job description
    all_skills = extract_skills(job_description)

    # Specific skills in preferred section
    preferred_skills = extract_skills(sections["preferred"])
    
    # Required skills are those in required section or all skills not strictly in preferred
    if preferred_skills:
        required_skills = [s for s in all_skills if s not in preferred_skills]
    else:
        required_skills = all_skills

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
        "total_skills_count": len(all_skills)
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
