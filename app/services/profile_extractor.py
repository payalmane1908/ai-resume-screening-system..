import re


def extract_profile_fields(text):
    raw = text or ""
    lower = raw.lower()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    # Extract contact details
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", raw)
    email = email_match.group(0) if email_match else ""

    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", raw)
    phone = phone_match.group(0) if phone_match else ""

    linkedin_match = re.search(r"linkedin\.com/in/[a-zA-Z0-9_-]+", lower)
    linkedin = "https://" + linkedin_match.group(0) if linkedin_match else ""

    # Detect sections for structure score
    detected_sections = {
        "projects": bool(re.search(r"\b(projects|portfolio|personal projects|key projects)\b", lower)),
        "experience": bool(re.search(r"\b(experience|work history|employment|career history|professional background)\b", lower)),
        "education": bool(re.search(r"\b(education|academic background|studies|university|degrees)\b", lower)),
        "skills": bool(re.search(r"\b(skills|technical skills|technologies|key skills|competencies)\b", lower))
    }

    achievements = [
        line
        for line in lines
        if re.search(r"\b(increased|reduced|improved|delivered|saved|optimized|launched|built)\b", line.lower())
        or re.search(r"\b\d+%|\$\d+|\b\d+\+?\s*(users|customers|projects|teams|clients)\b", line.lower())
    ]

    education = [
        line
        for line in lines
        if re.search(r"\b(bachelor|master|b\.tech|m\.tech|phd|university|college|degree)\b", line.lower())
    ]

    certifications = [
        line
        for line in lines
        if re.search(r"\b(certified|certification|aws certified|azure|gcp|scrum|pmp)\b", line.lower())
    ]

    experience_lines = [
        line
        for line in lines
        if re.search(r"\b(experience|years|worked|engineer|developer|analyst|intern)\b", line.lower())
    ]

    experience_text = "\n".join(experience_lines) if experience_lines else raw

    return {
        "full_text": raw,
        "experience_text": experience_text,
        "achievements": achievements,
        "education": education,
        "certifications": certifications,
        "has_cloud_keywords": bool(re.search(r"\b(aws|azure|gcp|cloud)\b", lower)),
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "detected_sections": detected_sections
    }
