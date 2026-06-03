import json
import logging
from flask import Blueprint, render_template, session, redirect, url_for
from app.services.database import get_connection
from app.services.analytics import skill_distribution, top_skill_gaps
from app.routes.screening import login_required

logger = logging.getLogger(__name__)

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics")
@login_required
def index():
    conn = get_connection()
    if session.get("role") == "Admin":
        rows = conn.execute(
            """
            SELECT id, name, matched_skills, missing_skills, final_score, years_experience, status
            FROM candidates
            """
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, name, matched_skills, missing_skills, final_score, years_experience, status
            FROM candidates
            WHERE user_id = ?
            """,
            (session["user_id"],)
        ).fetchall()
    conn.close()

    candidates = []
    for r in rows:
        candidates.append({
            "id": r["id"],
            "name": r["name"],
            "matched_skills": json.loads(r["matched_skills"] or "[]"),
            "missing_skills": json.loads(r["missing_skills"] or "[]"),
            "final_score": r["final_score"],
            "years_experience": r["years_experience"],
            "status": r["status"]
        })

    # Calculate skill frequency and gaps using analytics services
    skill_freq = skill_distribution(candidates)
    skill_gaps = top_skill_gaps(candidates, limit=10)

    # Average score
    avg_score = 0
    if candidates:
        avg_score = round(sum(c["final_score"] for c in candidates) / len(candidates), 1)

    # Average experience
    avg_exp = 0
    if candidates:
        avg_exp = round(sum(c["years_experience"] for c in candidates) / len(candidates), 1)

    # Status distribution
    status_counts = {"Pending": 0, "Selected": 0, "Rejected": 0}
    for c in candidates:
        status = c["status"]
        if status in status_counts:
            status_counts[status] += 1

    return render_template(
        "analytics.html",
        candidates=candidates,
        skill_freq=skill_freq,
        skill_gaps=skill_gaps,
        avg_score=avg_score,
        avg_exp=avg_exp,
        status_counts=status_counts
    )
