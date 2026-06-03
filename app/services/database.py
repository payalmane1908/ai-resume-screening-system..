import logging
import sqlite3
from contextlib import contextmanager

from config import Config

logger = logging.getLogger(__name__)


def get_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for safe database access.

    Usage:
        with get_db() as conn:
            conn.execute("SELECT ...")
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'HR',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    cursor.execute(
        """
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
            education TEXT,
            certifications TEXT,
            achievements TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    _ensure_candidate_columns(cursor)
    _ensure_user_columns(cursor)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jd_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            jd_text TEXT NOT NULL,
            required_skills TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS weight_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            keyword_weight REAL,
            semantic_weight REAL,
            experience_weight REAL,
            achievements_weight REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    _ensure_weight_history_columns(cursor)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS job_openings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            jd_text TEXT NOT NULL,
            min_experience REAL DEFAULT 0,
            status TEXT DEFAULT 'Open',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")


def _ensure_candidate_columns(cursor):
    cursor.execute("PRAGMA table_info(candidates)")
    existing = {row[1] for row in cursor.fetchall()}
    required_columns = {
        "user_id": "INTEGER",
        "source_file": "TEXT",
        "extracted_skills": "TEXT",
        "matched_skills": "TEXT",
        "missing_skills": "TEXT",
        "years_experience": "REAL DEFAULT 0",
        "keyword_score": "REAL DEFAULT 0",
        "semantic_score": "REAL DEFAULT 0",
        "experience_score": "REAL DEFAULT 0",
        "ai_summary": "TEXT",
        "ai_fit_score": "REAL",
        "tags": "TEXT",
        "ai_explanation": "TEXT",
        "strengths": "TEXT",
        "weaknesses": "TEXT",
        "rejection_reason": "TEXT",
        "ats_score": "REAL DEFAULT 0",
        "ats_formatting_issues": "TEXT",
        "ats_keyword_coverage": "REAL DEFAULT 0",
        "ats_suggestions": "TEXT",
        "fraud_stuffing_detected": "INTEGER DEFAULT 0",
        "fraud_suspicious_claims": "TEXT",
        "fraud_duplicate_content": "INTEGER DEFAULT 0",
        "fraud_authenticity_score": "REAL DEFAULT 100",
        "success_interview_prob": "REAL DEFAULT 0",
        "success_hiring_prob": "REAL DEFAULT 0",
        "success_readiness_score": "REAL DEFAULT 0",
        "questions_technical": "TEXT",
        "questions_project": "TEXT",
        "questions_behavioral": "TEXT",
        "questions_hr": "TEXT",
        "education": "TEXT",
        "certifications": "TEXT",
        "achievements": "TEXT",
        # SQLite ALTER TABLE does not allow non-constant defaults like CURRENT_TIMESTAMP.
        "created_at": "TEXT",
    }
    for column_name, column_type in required_columns.items():
        if column_name not in existing:
            cursor.execute(
                f"ALTER TABLE candidates ADD COLUMN {column_name} {column_type}"
            )


def _ensure_user_columns(cursor):
    cursor.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in cursor.fetchall()}
    if "role" not in existing:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'HR'")


def _ensure_weight_history_columns(cursor):
    cursor.execute("PRAGMA table_info(weight_history)")
    existing = {row[1] for row in cursor.fetchall()}
    if "user_id" not in existing:
        cursor.execute("ALTER TABLE weight_history ADD COLUMN user_id INTEGER")

