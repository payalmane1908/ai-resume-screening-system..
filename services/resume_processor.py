import json
import os
import pandas as pd
from werkzeug.utils import secure_filename

from config import Config
from services.parser import extract_text
from services.profile_extractor import extract_profile_fields
from services.semantic_matcher import semantic_score
from services.skill_extractor import extract_skills, highlight_skills
from services.scorer import (
    achievements_score,
    extract_years_of_experience,
    experience_score,
    rank_candidates,
    skill_match_score,
    weighted_score,
)


ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "csv"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage):
    filename = secure_filename(file_storage.filename)
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file_storage.save(file_path)
    return filename, file_path


def _first_non_empty(row, keys, default=""):
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() != "nan":
            return text
    return default


def _normalize_name(raw_name, fallback):
    cleaned = " ".join(str(raw_name).replace("_", " ").split()).strip()
    if not cleaned:
        return fallback
    return cleaned.title()


def _candidate_result(name, source_file, resume_text, jd_text, jd_skills, min_experience, weights=None):
    profile = extract_profile_fields(resume_text)
    resume_skills = extract_skills(resume_text)
    keyword, matched, missing = skill_match_score(resume_skills, jd_skills)
    
    # AI Enhancement: Auto-tagging skills
    tags = [s for s in resume_skills if s in jd_skills]
    
    semantic_global = semantic_score(resume_text, jd_text)
    semantic_experience = semantic_score(profile["experience_text"], jd_text)
    semantic_achievements = semantic_score("\n".join(profile["achievements"]), jd_text)
    semantic = round((0.6 * semantic_global) + (0.25 * semantic_experience) + (0.15 * semantic_achievements), 2)
    
    # AI Enhancement: Fit Prediction logic
    fit_score = round((semantic * 0.7) + (keyword * 0.3), 2)
    
    # AI Enhancement: Simple Summarization
    summary = resume_text[:200].replace("\n", " ").strip() + "..."
    
    years = extract_years_of_experience(resume_text)
    exp_score = experience_score(years, min_experience)
    ach_score = achievements_score(profile["achievements"])
    final = weighted_score(keyword, semantic, exp_score, ach_score, weights)
    
    # Explainable AI: Strengths & Weaknesses
    strengths = []
    weaknesses = []
    
    if len(matched) > 5: strengths.append(f"Strong skill alignment with {len(matched)} matching keywords.")
    if semantic > 75: strengths.append("High contextual relevance to the job requirements.")
    if years >= min_experience: strengths.append(f"Meets or exceeds experience requirement ({years} years).")
    
    if len(missing) > 3: weaknesses.append(f"Missing key technical skills: {', '.join(missing[:3])}")
    if semantic < 50: weaknesses.append("Low semantic similarity to the job description.")
    if years < min_experience: weaknesses.append(f"Experience ({years}y) is below the target ({min_experience}y).")

    # Rejection Reasoning (Why Not Selected)
    rejection_reason = None
    if final < 60:
        if years < min_experience: rejection_reason = "Insufficient years of relevant experience."
        elif semantic < 50: rejection_reason = "Contextual fit does not align with role responsibilities."
        else: rejection_reason = "Overall score below threshold for current batch."

    # Final Natural Language Explanation
    explanation = f"This candidate scored {final}% primarily due to "
    if keyword > 70: explanation += f"excellent direct alignment with {len(matched)} key skills. "
    elif semantic > 70: explanation += "high contextual relevance to the role's requirements. "
    else: explanation += "a balanced mix of skills and experience. "
    
    if years >= min_experience:
        explanation += f"They meet the seniority requirement with {years} years of experience."
    else:
        explanation += f"While they have {years} years of experience, they are slightly below the target of {min_experience}."

    return {
        "name": name,
        "source_file": source_file,
        "resume_text": resume_text,
        "resume_preview": highlight_skills(resume_text[:3500], matched),
        "extracted_skills": resume_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "keyword_score": keyword,
        "semantic_score": semantic,
        "years_experience": years,
        "experience_score": exp_score,
        "achievements_score": ach_score,
        "education": profile["education"],
        "certifications": profile["certifications"],
        "achievements": profile["achievements"],
        "final_score": final,
        "ai_summary": summary,
        "ai_fit_score": fit_score,
        "tags": tags,
        "ai_explanation": explanation,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "rejection_reason": rejection_reason
    }


def process_files(files, jd_text, min_experience=2, weights=None):
    jd_skills = extract_skills(jd_text)
    candidates = []
    errors = []

    for idx, incoming in enumerate(files, start=1):
        if not incoming or not incoming.filename:
            continue
        if not allowed_file(incoming.filename):
            errors.append(f"{incoming.filename}: unsupported format")
            continue

        try:
            filename, file_path = save_upload(incoming)
            ext = filename.rsplit(".", 1)[1].lower()
            if ext == "csv":
                df = pd.read_csv(file_path)
                df.columns = [c.lower().strip() for c in df.columns]
                for row_i, row in df.iterrows():
                    resume_text = _first_non_empty(
                        row,
                        ["resume_str", "resume_text", "resume", "profile", "cv_text", "content"],
                    )
                    if not resume_text:
                        errors.append(
                            f"{filename} row {row_i + 2}: missing resume text (expected resume_str/resume_text/resume)"
                        )
                        continue
                    raw_name = _first_non_empty(
                        row,
                        ["name", "candidate_name", "full_name", "applicant_name", "username"],
                    )
                    row_id = _first_non_empty(
                        row,
                        ["id", "candidate_id", "applicant_id", "user_id"],
                    )
                    fallback = f"Candidate {row_id}" if row_id else f"Candidate {idx}-{row_i + 1}"
                    name = _normalize_name(raw_name, fallback)
                    candidates.append(
                        _candidate_result(name, filename, resume_text, jd_text, jd_skills, min_experience, weights)
                    )
            else:
                resume_text = extract_text(file_path)
                if not resume_text or resume_text == "Unsupported file format":
                    raise ValueError("Unable to parse resume text")
                name = os.path.splitext(filename)[0].replace("_", " ").title()
                candidates.append(
                    _candidate_result(name, filename, resume_text, jd_text, jd_skills, min_experience, weights)
                )
        except Exception as exc:
            errors.append(f"{incoming.filename}: {exc}")

    return rank_candidates(candidates), errors, jd_skills


def serialize_list(values):
    return json.dumps(values or [])
