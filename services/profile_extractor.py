import re


def extract_profile_fields(text):
    raw = text or ""
    lower = raw.lower()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

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
    }
