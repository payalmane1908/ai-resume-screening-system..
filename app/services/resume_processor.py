import json
import os
import pandas as pd
from werkzeug.utils import secure_filename

from config import Config
from app.services.parser import extract_text
from app.services.profile_extractor import extract_profile_fields
from app.services.semantic_matcher import semantic_score
from app.services.skill_extractor import extract_skills, highlight_skills
from app.services.scorer import (
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
    
    years = extract_years_of_experience(resume_text)
    exp_score = experience_score(years, min_experience)
    ach_score = achievements_score(profile["achievements"])
    final = weighted_score(keyword, semantic, exp_score, ach_score, weights)
    
    # 1. Dynamic Natural Language Explanation & Recommendations
    recommendation = "Highly Recommended" if final >= 80 else "Recommended" if final >= 65 else "Consider with Reservations" if final >= 50 else "Not Recommended"
    
    # 2. Build a dynamic, personalized AI Summary
    summary_parts = []
    if profile["education"]:
        deg = profile["education"][0].split(",")[0].split(" at ")[0].strip()
        summary_parts.append(f"Educated background in {deg}.")
    if years > 0:
        summary_parts.append(f"Brings {years} years of professional experience.")
    else:
        summary_parts.append("Fresh applicant with academic project experience.")
        
    focus = [s.title() for s in resume_skills[:3]]
    if focus:
        summary_parts.append(f"Demonstrates core competencies in {', '.join(focus)}.")
    if profile["certifications"]:
        cert_name = profile["certifications"][0].replace("Certified", "").strip()
        summary_parts.append(f"Certified in {cert_name[:40]}.")
        
    summary_parts.append(f"Recommended action: {recommendation} for interview.")
    summary = " ".join(summary_parts)

    # 3. Build dynamic, candidate-specific Strengths & Weaknesses
    strengths = []
    weaknesses = []
    
    if matched:
        strengths.append(f"Technical expertise matches required stack: {', '.join(matched[:3])}")
    if profile["certifications"]:
        strengths.append(f"Holds industry credentials: {profile['certifications'][0][:60]}")
    if profile["achievements"]:
        highlight = profile["achievements"][0][:70].strip()
        strengths.append(f"Proven results: {highlight}...")
    if years >= min_experience and years > 0:
        strengths.append(f"Meets seniority targets with {years} years of background.")
    if semantic >= 70:
        strengths.append("High semantic alignment with JD responsibilities.")
    if profile.get("email") and profile.get("phone"):
        strengths.append("Professional contact information is fully present.")
    if profile.get("detected_sections", {}).get("skills"):
        strengths.append("Skills section is clearly structured and defined.")
        
    if missing:
        for ms in missing[:3]:
            weaknesses.append(f"Missing critical skill: {ms.title()}")
    if years < min_experience:
        weaknesses.append(f"Years of experience ({years}y) is below target of {min_experience}y.")
    if not profile["achievements"]:
        weaknesses.append("Resume does not list measurable achievements or metrics.")
    if not profile.get("detected_sections", {}).get("projects"):
        weaknesses.append("Structure issues: Missing a dedicated Projects Section.")
    if not profile.get("detected_sections", {}).get("experience"):
        weaknesses.append("Structure issues: Work experience section is poorly formatted.")

    # Rejection Reasoning (Why Not Selected)
    rejection_reason = None
    if final < 60:
        if years < min_experience: rejection_reason = "Insufficient years of relevant experience."
        elif semantic < 50: rejection_reason = "Contextual fit does not align with role responsibilities."
        else: rejection_reason = "Overall score below threshold for current batch."

    # Dynamic explanation
    explanation_parts = [
        f"Candidate exhibits a final matching score of {final}%.",
        f"This is driven by a {keyword}% keyword alignment and a {semantic}% semantic fit score.",
        f"The candidate is {recommendation.lower()} based on their {years} years of experience and skill matches.",
        f"Action: Move to {('technical interview' if final >= 70 else 'HR screening' if final >= 50 else 'hold status')}."
    ]
    explanation = " ".join(explanation_parts)

    # 4. ATS Compatibility Checker
    ats_formatting_issues = []
    ats_suggestions = []
    
    contact_score = 0
    if profile.get("email"):
        contact_score += 7
    else:
        ats_formatting_issues.append("Missing email contact details in resume header.")
        ats_suggestions.append("Add email address to the resume header for recruiter contact.")
        
    if profile.get("phone"):
        contact_score += 7
    else:
        ats_formatting_issues.append("Missing phone number in contact details.")
        ats_suggestions.append("Include a valid mobile number under your name.")
        
    if profile.get("linkedin"):
        contact_score += 6
    else:
        ats_formatting_issues.append("Missing LinkedIn professional profile link.")
        ats_suggestions.append("Add a LinkedIn URL to link to your professional web profile.")

    struct_score = 0
    for sect, detected in profile.get("detected_sections", {}).items():
        if detected:
            struct_score += 5
        else:
            ats_formatting_issues.append(f"Missing {sect.capitalize()} Section header.")
            ats_suggestions.append(f"Create a dedicated, clearly titled '{sect.capitalize()}' section in the resume.")

    format_score = 0
    ext = source_file.split(".")[-1].lower() if source_file else ""
    if ext in ["pdf", "docx"]:
        format_score += 10
    else:
        ats_formatting_issues.append("Using plain text format - recommend PDF or DOCX for optimal ATS parsing.")
        ats_suggestions.append("Save and export the resume as a standard PDF or DOCX file.")
        
    w_count = len(resume_text.split())
    if 250 <= w_count <= 1500:
        format_score += 10
    else:
        if w_count < 250:
            ats_formatting_issues.append("Resume word count is low. Add detailed project scopes.")
            ats_suggestions.append("Expand on your work experience and achievements to reach 300+ words.")
        else:
            ats_formatting_issues.append("Resume is too long. Condense sections.")
            ats_suggestions.append("Condense work description to keep the resume under 2 pages (max 1500 words).")

    ats_keyword_coverage = round((len(matched) / max(1, len(jd_skills))) * 100, 1)
    kw_contrib = (ats_keyword_coverage / 100.0) * 40.0

    ats_score = round(contact_score + struct_score + format_score + kw_contrib, 1)
    ats_score = min(100.0, max(10.0, ats_score))
    
    if missing:
        ats_suggestions.append(f"Incorporate missing keywords to improve ATS match: {', '.join(missing[:3])}.")

    # 5. Fraud Detection
    fraud_stuffing_detected = 0
    stuffing_skills = []
    lower_text = resume_text.lower()
    for skill in resume_skills:
        count = lower_text.count(skill.lower())
        if count > 5:
            fraud_stuffing_detected = 1
            stuffing_skills.append(skill)
            
    fraud_suspicious_claims = []
    if "fastapi" in resume_skills and years > 8:
        fraud_suspicious_claims.append("Claiming experience in FastAPI that exceeds the framework's historical release date.")
    if "kubernetes" in resume_skills and years > 12:
        fraud_suspicious_claims.append("Claiming experience in Kubernetes that exceeds the tool's historical release date.")
        
    lines = [l.strip() for l in resume_text.splitlines() if len(l.strip()) > 30]
    unique_lines = set(lines)
    fraud_duplicate_content = 1 if len(lines) - len(unique_lines) > 3 else 0
    
    fraud_authenticity_score = 100.0
    if fraud_stuffing_detected: 
        fraud_authenticity_score -= 15.0
    if fraud_suspicious_claims: 
        fraud_authenticity_score -= 10.0 * len(fraud_suspicious_claims)
    if fraud_duplicate_content: 
        fraud_authenticity_score -= 15.0
    fraud_authenticity_score = max(0.0, fraud_authenticity_score)

    # 6. Candidate Success Prediction
    success_interview_prob = round(min(100.0, (semantic * 0.45) + (keyword * 0.35) + (ats_score * 0.20)), 1)
    success_hiring_prob = round(min(100.0, (final * 0.60) + (exp_score * 0.25) + (ach_score * 0.15)), 1)
    success_readiness_score = round(min(100.0, (keyword * 0.50) + (exp_score * 0.50)), 1)

    # 7. AI Interview Question Generator
    questions_technical = []
    if "python" in resume_skills:
        questions_technical.append("Explain the memory management model and GIL limitations in Python.")
        questions_technical.append("How do you use decorators, generators, and context managers to optimize memory consumption in Python?")
    if "react" in resume_skills or "javascript" in resume_skills or "frontend" in lower_text:
        questions_technical.append("What are React concurrent rendering features and how do you handle state optimization?")
        questions_technical.append("Explain the Virtual DOM reconciliation algorithm and how React Fiber optimizes updates.")
    if "machine learning" in resume_skills or "data science" in lower_text:
        questions_technical.append("How do you select loss functions and avoid overfitting in neural networks?")
        questions_technical.append("What are the advantages of transformer-based architectures for NLP tasks compared to traditional LSTMs?")
    
    if len(questions_technical) < 3:
        main_skill = matched[0] if matched else (resume_skills[0] if resume_skills else "software engineering")
        questions_technical.append(f"Walk me through the system architecture and best practices using {main_skill}.")
        questions_technical.append(f"How do you handle unit testing, caching, and profiling for systems using {main_skill}?")
        questions_technical.append("Explain standard scalability strategies and how you optimize slow database operations.")

    questions_project = [
        "What was the most challenging technical bottleneck in your projects, and how did you resolve it?",
        "How did you design the schema, data flow, and services integration for your portfolio systems?",
        "Walk me through how you would handle scaling a REST API to support 10x traffic increase."
    ]
    questions_behavioral = [
        "Tell me about a time you had to deliver a high-stakes feature under a tight launch deadline.",
        "How do you handle design disagreements or code review disputes within your development team?",
        "Give an example of a mistake you made in a previous role. How did you communicate it and what did you learn?"
    ]
    questions_hr = [
        "Why does this company and the target role match your career aspirations at this point?",
        f"How do your {years} years of technical experience prepare you for this role's responsibilities?",
        "What are your core expectations for engineering leadership and team culture?"
    ]

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
        "rejection_reason": rejection_reason,
        "ats_score": ats_score,
        "ats_formatting_issues": ats_formatting_issues,
        "ats_keyword_coverage": ats_keyword_coverage,
        "ats_suggestions": ats_suggestions,
        "fraud_stuffing_detected": fraud_stuffing_detected,
        "fraud_suspicious_claims": fraud_suspicious_claims,
        "fraud_duplicate_content": fraud_duplicate_content,
        "fraud_authenticity_score": fraud_authenticity_score,
        "success_interview_prob": success_interview_prob,
        "success_hiring_prob": success_hiring_prob,
        "success_readiness_score": success_readiness_score,
        "questions_technical": questions_technical,
        "questions_project": questions_project,
        "questions_behavioral": questions_behavioral,
        "questions_hr": questions_hr
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
