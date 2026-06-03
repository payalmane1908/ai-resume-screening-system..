-- HireMind AI Database Schema
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'HR',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    source_file TEXT,
    resume_text TEXT NOT NULL,
    extracted_skills TEXT,
    matched_skills TEXT,
    missing_skills TEXT,
    years_experience REAL DEFAULT 0,
    keyword_score REAL DEFAULT 0,
    semantic_score REAL DEFAULT 0,
    experience_score REAL DEFAULT 0,
    final_score REAL DEFAULT 0,
    rank INTEGER,
    status TEXT DEFAULT 'Pending',
    ai_summary TEXT,
    ai_fit_score REAL,
    tags TEXT,
    ai_explanation TEXT,
    strengths TEXT,
    weaknesses TEXT,
    rejection_reason TEXT,
    ats_score REAL DEFAULT 0,
    ats_formatting_issues TEXT,
    ats_keyword_coverage REAL DEFAULT 0,
    ats_suggestions TEXT,
    fraud_stuffing_detected INTEGER DEFAULT 0,
    fraud_suspicious_claims TEXT,
    fraud_duplicate_content INTEGER DEFAULT 0,
    fraud_authenticity_score REAL DEFAULT 100,
    success_interview_prob REAL DEFAULT 0,
    success_hiring_prob REAL DEFAULT 0,
    success_readiness_score REAL DEFAULT 0,
    questions_technical TEXT,
    questions_project TEXT,
    questions_behavioral TEXT,
    questions_hr TEXT,
    education TEXT,
    certifications TEXT,
    achievements TEXT,
    created_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
