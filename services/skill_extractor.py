import re


SKILL_SYNONYMS = {
    "python": ["python", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "sql": ["sql", "postgresql", "mysql", "sqlite", "pl/sql"],
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
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch", "torch"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "java": ["java"],
    "c++": ["c++", "cpp"],
    "mongodb": ["mongodb", "mongo"],
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