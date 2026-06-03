import re


SKILL_SYNONYMS = {
    "python": ["python", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "sql": ["sql", "postgresql", "mysql", "sqlite", "pl/sql", "oracle", "mariadb"],
    "machine learning": ["machine learning", "ml", "predictive modeling"],
    "deep learning": ["deep learning", "dl", "neural network", "neural networks"],
    "nlp": ["nlp", "natural language processing"],
    "data analysis": ["data analysis", "data analytics", "analytics"],
    "aws": ["aws", "amazon web services"],
    "docker": ["docker", "containerization", "containers"],
    "flask": ["flask"],
    "django": ["django"],
    "react": ["react", "reactjs", "react.js"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch", "torch"],
    "html": ["html", "html5"],
    "css": ["css", "css3", "sass", "scss"],
    "java": ["java"],
    "c++": ["c++", "cpp"],
    "mongodb": ["mongodb", "mongo"],
    "kubernetes": ["kubernetes", "k8s"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure"],
    "fastapi": ["fastapi"],
    "nodejs": ["node.js", "nodejs", "node"],
    "typescript": ["typescript", "ts"],
    "git": ["git", "github", "gitlab"],
    "ci/cd": ["ci/cd", "continuous integration", "github actions", "jenkins"],
    "golang": ["go", "golang"],
}


def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9+\s]", " ", (text or "").lower())


def extract_skills(text):
    cleaned_text = clean_text(text)
    found = set()
    for canonical, synonyms in SKILL_SYNONYMS.items():
        for variant in synonyms:
            pattern = r"\b" + re.escape(variant.lower()) + r"\b"
            if re.search(pattern, cleaned_text):
                found.add(canonical)
                break
    return sorted(found)


def highlight_skills(text, skills):
    highlighted = text or ""
    for skill in sorted(skills, key=len, reverse=True):
        pattern = re.compile(rf"(?i)\b({re.escape(skill)})\b")
        highlighted = pattern.sub(r"<mark>\1</mark>", highlighted)
    return highlighted