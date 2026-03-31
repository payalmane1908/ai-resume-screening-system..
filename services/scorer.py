import re


WEIGHTS = {
    "keyword": 0.4,
    "semantic": 0.35,
    "experience": 0.15,
    "achievements": 0.10,
}


def normalize_weights(custom_weights=None):
    if not custom_weights:
        return WEIGHTS.copy()
    merged = WEIGHTS.copy()
    for key in merged:
        if key in custom_weights:
            try:
                merged[key] = max(0.0, float(custom_weights[key]))
            except (TypeError, ValueError):
                pass
    total = sum(merged.values())
    if total <= 0:
        return WEIGHTS.copy()
    return {k: v / total for k, v in merged.items()}


def skill_match_score(resume_skills, jd_skills):
    if not jd_skills:
        return 0.0, [], []
    resume_set = set(resume_skills)
    jd_set = set(jd_skills)
    matched = sorted(resume_set.intersection(jd_set))
    missing = sorted(jd_set - resume_set)
    score = (len(matched) / max(1, len(jd_set))) * 100
    return round(score, 2), matched, missing


def extract_years_of_experience(resume_text):
    text = (resume_text or "").lower()
    patterns = [r"(\d+(?:\.\d+)?)\+?\s+years", r"experience\s+of\s+(\d+(?:\.\d+)?)"]
    best = 0.0
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            best = max(best, float(match))
    return best


def experience_score(years, target_years):
    if target_years <= 0:
        return 100.0
    score = min(100.0, (years / target_years) * 100)
    return round(score, 2)


def achievements_score(achievement_lines):
    count = len(achievement_lines or [])
    return round(min(100.0, count * 20.0), 2)


def weighted_score(keyword, semantic, exp, achievements=0.0, weights=None):
    effective_weights = normalize_weights(weights)
    
    # Advanced Fit Score: Multi-dimensional integration
    # Combining direct matches (keyword), contextual relevance (semantic), and professional depth (experience/achievements)
    
    total = (
        effective_weights["keyword"] * keyword
        + effective_weights["semantic"] * semantic
        + effective_weights["experience"] * exp
        + effective_weights["achievements"] * achievements
    )
    
    # AI Fit Adjustment: Penalize if key criteria are missing even if total is high
    if keyword < 20 and semantic < 30:
        total *= 0.7  # "Low Relevance" penalty
    elif keyword > 80 and semantic > 80:
        total = min(100.0, total * 1.1)  # "Perfect Match" bonus
        
    return round(total, 2)


def rank_candidates(candidates):
    ranked = sorted(candidates, key=lambda c: c["final_score"], reverse=True)
    for idx, candidate in enumerate(ranked, start=1):
        candidate["rank"] = idx
    return ranked