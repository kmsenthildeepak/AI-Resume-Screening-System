# Configuration and Constants for AI Resume Screening System

from typing import Dict, List, Set

# File constraints
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Scoring weights (Configurable)
DEFAULT_WEIGHT_TEXT_SIMILARITY = 0.65
DEFAULT_WEIGHT_SKILL_MATCH = 0.35

# Category weights for skill matching (when both required and preferred skills are present)
DEFAULT_REQUIRED_SKILL_WEIGHT = 0.80
DEFAULT_PREFERRED_SKILL_WEIGHT = 0.20

# Text length constraints
MIN_JOB_DESCRIPTION_CHARS = 30
MAX_TEXT_PREVIEW_CHARS = 1000

# Canonical skill taxonomy mapping aliases/synonyms to standardized skill names
SKILL_TAXONOMY: Dict[str, List[str]] = {
    # Programming Languages
    "Python": ["python", "py", "python3"],
    "Java": ["java", "core java", "java 8", "java 11", "java 17"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp", "c sharp"],
    "JavaScript": ["javascript", "js", "ecmascript"],
    "TypeScript": ["typescript", "ts"],
    "Go": ["golang", "go language"],
    "Rust": ["rust", "rustlang"],
    "Ruby": ["ruby", "ruby on rails", "rails"],
    "PHP": ["php"],
    "SQL": ["sql", "structured query language"],
    "R": ["r programming", "r language"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift"],

    # Web & Backend Frameworks
    "Spring Boot": ["spring boot", "springboot", "spring framework", "spring mvc"],
    "Django": ["django", "django rest framework", "drf"],
    "FastAPI": ["fastapi", "fast api"],
    "Flask": ["flask"],
    "Node.js": ["nodejs", "node.js", "node js"],
    "Express.js": ["express", "expressjs", "express.js"],
    "React": ["react", "reactjs", "react.js", "react native"],
    "Angular": ["angular", "angularjs"],
    "Vue.js": ["vue", "vuejs", "vue.js"],
    "ASP.NET": ["asp.net", "asp net", "dotnet", ".net", ".net core"],
    "REST API": ["rest", "restful", "rest api", "restful api", "rest apis"],
    "GraphQL": ["graphql"],
    "Microservices": ["microservices", "microservice architecture", "micro-services"],

    # Machine Learning & Data Science
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning"],
    "Natural Language Processing": ["nlp", "natural language processing"],
    "Scikit-Learn": ["scikit-learn", "scikit learn", "sklearn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch", "torch"],
    "Computer Vision": ["computer vision", "opencv"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Data Analysis": ["data analysis", "data analytics", "data mining"],
    "Data Visualization": ["data visualization", "matplotlib", "seaborn", "tableau", "power bi"],

    # Cloud, DevOps & Databases
    "Docker": ["docker", "containerization", "containers"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "CI/CD": ["ci/cd", "ci-cd", "continuous integration", "continuous deployment", "jenkins", "github actions", "gitlab ci"],
    "Git": ["git", "github", "gitlab"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Kafka": ["kafka", "apache kafka"],
    "Linux": ["linux", "unix", "ubuntu", "bash", "shell scripting"],

    # Soft Skills & Methodologies
    "Agile": ["agile", "scrum", "kanban", "sprint"],
    "Problem Solving": ["problem solving", "analytical thinking", "analytical skills"],
    "Communication": ["communication", "team communication", "presentation skills"],
    "Leadership": ["leadership", "mentoring", "team lead"],
    "Teamwork": ["teamwork", "collaboration", "cross-functional collaboration"],
    "Project Management": ["project management", "jira"]
}

# Inverted index for fast skill alias lookup: alias -> canonical_skill
ALIAS_TO_SKILL: Dict[str, str] = {}
for canonical, aliases in SKILL_TAXONOMY.items():
    ALIAS_TO_SKILL[canonical.lower()] = canonical
    for alias in aliases:
        ALIAS_TO_SKILL[alias.lower()] = canonical

# Degree and education keywords for extraction
EDUCATION_KEYWORDS = [
    "bachelor", "bachelors", "b.tech", "btech", "b.e", "be", "b.s", "bs",
    "master", "masters", "m.tech", "mtech", "m.e", "me", "m.s", "ms",
    "ph.d", "phd", "doctorate", "degree", "diploma", "computer science",
    "information technology", "data science", "software engineering",
    "electrical engineering", "electronics", "high school"
]

# Experience keywords for extraction
EXPERIENCE_KEYWORDS = [
    "experience", "years of experience", "work history", "employment",
    "internship", "developer", "engineer", "lead", "architect", "analyst",
    "manager", "consultant", "specialist"
]
