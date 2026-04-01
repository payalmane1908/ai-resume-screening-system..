import io
import json
from functools import wraps

import pandas as pd
from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services.database import get_connection
from services.resume_processor import process_files, serialize_list
from services.notifications import send_email_alert, send_slack_alert

screening_bp = Blueprint("screening", __name__)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "Admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("screening.dashboard"))
        return view_func(*args, **kwargs)

    return wrapper


@screening_bp.route("/")
@login_required
def index():
    # Log view action
    conn = get_connection()
    conn.execute(
        "INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)",
        (session["user_id"], "VIEW_UPLOAD", "User visited screening page")
    )
    conn.commit()
    
    templates = conn.execute(
        "SELECT id, name, jd_text FROM jd_templates ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template("index.html", templates=templates)


@screening_bp.route("/templates", methods=["POST"])
@login_required
def create_template():
    name = request.form.get("template_name", "").strip()
    jd_text = request.form.get("template_jd", "").strip()
    required_skills = request.form.get("template_skills", "").strip()
    if not (name and jd_text):
        flash("Template name and JD are required.", "warning")
        return redirect(url_for("screening.index"))

    conn = get_connection()
    conn.execute(
        "INSERT INTO jd_templates (name, jd_text, required_skills) VALUES (?, ?, ?)",
        (name, jd_text, required_skills),
    )
    conn.commit()
    conn.close()
    flash("JD template saved.", "success")
    return redirect(url_for("screening.index"))


@screening_bp.route("/api/screen", methods=["POST"])
@login_required
def screen_bulk():
    try:
        files = request.files.getlist("files")
        jd_text = request.form.get("jd", "").strip()
        try:
            min_experience = float(request.form.get("min_experience", 2) or 2)
        except ValueError:
            return jsonify({"ok": False, "error": "Minimum experience must be a number."}), 400
        custom_weights = {
            "keyword": request.form.get("weight_keyword", 40),
            "semantic": request.form.get("weight_semantic", 35),
            "experience": request.form.get("weight_experience", 15),
            "achievements": request.form.get("weight_achievements", 10),
        }
        replace_existing = request.form.get("replace_existing", "true").lower() == "true"

        if not files:
            return jsonify({"ok": False, "error": "No files selected."}), 400
        if not jd_text:
            return jsonify({"ok": False, "error": "Job description is required."}), 400

        candidates, errors, jd_skills = process_files(files, jd_text, min_experience, custom_weights)
        if not candidates:
            return jsonify({"ok": False, "error": "No valid resumes found.", "errors": errors}), 400

        conn = get_connection()
        # Save weight history
        conn.execute(
            """
            INSERT INTO weight_history (keyword_weight, semantic_weight, experience_weight, achievements_weight)
            VALUES (?, ?, ?, ?)
            """,
            (
                custom_weights["keyword"],
                custom_weights["semantic"],
                custom_weights["experience"],
                custom_weights["achievements"],
            ),
        )
        if replace_existing:
            conn.execute("DELETE FROM candidates")

        for c in candidates:
            conn.execute(
                """
                INSERT INTO candidates (
                    name, source_file, resume_text, extracted_skills, matched_skills, missing_skills,
                    years_experience, keyword_score, semantic_score, experience_score, final_score, rank, status,
                    ai_summary, ai_fit_score, tags, ai_explanation, strengths, weaknesses, rejection_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    c["name"],
                    c["source_file"],
                    c["resume_text"],
                    serialize_list(c["extracted_skills"]),
                    serialize_list(c["matched_skills"]),
                    serialize_list(c["missing_skills"]),
                    c["years_experience"],
                    c["keyword_score"],
                    c["semantic_score"],
                    c["experience_score"],
                    c["final_score"],
                    c["rank"],
                    "Pending",
                    c.get("ai_summary"),
                    c.get("ai_fit_score"),
                    serialize_list(c.get("tags")),
                    c.get("ai_explanation"),
                    serialize_list(c.get("strengths")),
                    serialize_list(c.get("weaknesses")),
                    c.get("rejection_reason"),
                ),
            )
        conn.commit()
        conn.close()
        
        # New Feature: Trigger Alerts for Top Candidates
        if candidates and candidates[0]["final_score"] >= 85:
            top_c = candidates[0]
            # Slack alert
            send_slack_alert(top_c["name"], top_c["final_score"], jd_text[:50] + "...")
            # Email alert (if HR email configured)
            hr_email = "hr@example.com" # Should be in config/session
            send_email_alert(hr_email, top_c["name"], top_c["final_score"], jd_text[:50] + "...")

        return jsonify(
            {
                "ok": True,
                "processed": len(candidates),
                "errors": errors,
                "jd_skills": jd_skills,
                "top_candidate": candidates[0]["name"] if candidates else None,
            }
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Server error while screening: {exc}"}), 500


@screening_bp.route("/dashboard")
@login_required
def dashboard():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, name, source_file, resume_text, matched_skills, missing_skills,
               keyword_score, semantic_score, experience_score, final_score, rank, status,
               ai_summary, ai_fit_score, tags, ai_explanation, strengths, weaknesses, rejection_reason
        FROM candidates
        ORDER BY rank ASC
        """
    ).fetchall()
    conn.close()

    candidates = []
    skill_frequency = {}
    for row in rows:
        matched = json.loads(row["matched_skills"] or "[]")
        missing = json.loads(row["missing_skills"] or "[]")
        tags = json.loads(row["tags"] or "[]")
        for s in matched:
            skill_frequency[s] = skill_frequency.get(s, 0) + 1
        candidates.append(
            {
                "id": row["id"],
                "name": row["name"],
                "source_file": row["source_file"],
                "resume_text": row["resume_text"][:3500],
                "matched_skills": matched,
                "missing_skills": missing,
                "keyword_score": row["keyword_score"],
                "semantic_score": row["semantic_score"],
                "experience_score": row["experience_score"],
                "final_score": row["final_score"],
                "rank": row["rank"],
                "status": row["status"],
                "ai_summary": row["ai_summary"],
                "ai_fit_score": row["ai_fit_score"],
                "tags": tags,
                "ai_explanation": row["ai_explanation"],
                "strengths": json.loads(row["strengths"] or "[]"),
                "weaknesses": json.loads(row["weaknesses"] or "[]"),
                "rejection_reason": row["rejection_reason"]
            }
        )

    return render_template(
        "dashboard.html",
        candidates=candidates,
        skill_frequency=skill_frequency,
    )


@screening_bp.route("/download/csv-template")
@login_required
def download_csv_template():
    sample = pd.DataFrame(
        [
            {
                "id": "C001",
                "name": "John Doe",
                "resume_text": "Python developer with 3 years experience in Flask and NLP...",
            },
            {
                "id": "C002",
                "name": "Jane Smith",
                "resume_text": "Data analyst with SQL, dashboards, and cloud deployment exposure...",
            },
        ]
    )
    output = io.StringIO()
    sample.to_csv(output, index=False)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=resume_upload_template.csv"},
    )


@screening_bp.route("/api/weights/history")
@login_required
def get_weight_history():
    conn = get_connection()
    history = conn.execute(
        "SELECT keyword_weight, semantic_weight, experience_weight, achievements_weight, created_at FROM weight_history ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "history": [dict(h) for h in history]})


@screening_bp.route("/api/weights/suggest")
@login_required
def suggest_weights():
    # Simulate AI suggestions based on dummy data
    suggestions = {
        "Tech-heavy": {"keyword": 40, "semantic": 40, "experience": 10, "achievements": 10},
        "Managerial": {"keyword": 20, "semantic": 30, "experience": 30, "achievements": 20},
        "Internship": {"keyword": 50, "semantic": 30, "experience": 5, "achievements": 15},
    }
    return jsonify({"ok": True, "suggestions": suggestions})


@screening_bp.route("/api/skill-gap/<int:candidate_id>")
@login_required
def get_skill_gap(candidate_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT matched_skills, missing_skills FROM candidates WHERE id = ?", (candidate_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"ok": False, "error": "Candidate not found"}), 404
    return jsonify({
        "ok": True,
        "matched": json.loads(row["matched_skills"] or "[]"),
        "missing": json.loads(row["missing_skills"] or "[]")
    })


@screening_bp.route("/update-status/<int:candidate_id>", methods=["POST"])
@login_required
@admin_required
def update_status(candidate_id):
    status = request.form.get("status", "Pending")
    if status not in {"Pending", "Selected", "Rejected"}:
        return jsonify({"ok": False, "error": "Invalid status"}), 400

    conn = get_connection()
    conn.execute("UPDATE candidates SET status = ? WHERE id = ?", (status, candidate_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@screening_bp.route("/export/excel")
@login_required
def export_excel():
    conn = get_connection()
    rows = conn.execute(
        "SELECT name, source_file, keyword_score, semantic_score, experience_score, final_score, rank, status FROM candidates ORDER BY rank ASC"
    ).fetchall()
    conn.close()
    df = pd.DataFrame([dict(r) for r in rows])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Candidates")
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=candidates.xlsx"},
    )


@screening_bp.route("/export/pdf")
@login_required
def export_pdf():
    conn = get_connection()
    rows = conn.execute(
        "SELECT rank, name, final_score, status FROM candidates ORDER BY rank ASC"
    ).fetchall()
    conn.close()

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        output = io.BytesIO()
        pdf = canvas.Canvas(output, pagesize=A4)
        y = 800
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, y, "AI Resume Screening Report")
        y -= 30
        pdf.setFont("Helvetica", 11)
        for r in rows:
            line = f"#{r['rank']} - {r['name']} | Score: {r['final_score']} | Status: {r['status']}"
            pdf.drawString(40, y, line[:100])
            y -= 20
            if y <= 60:
                pdf.showPage()
                y = 800
        pdf.save()
        output.seek(0)
        payload = output.getvalue()
    except Exception:
        payload = b"Install reportlab for rich PDF export."

    return Response(
        payload,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=candidates-report.pdf"},
    )
