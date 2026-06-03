import io
import json
import logging
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

from config import Config
from app.services.database import get_connection
from app.services.notifications import send_email_alert, send_slack_alert
from app.services.resume_processor import process_files, serialize_list

logger = logging.getLogger(__name__)

VALID_STATUSES = {"Pending", "Selected", "Rejected"}

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
    conn = get_connection()
    conn.execute(
        "INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)",
        (session["user_id"], "VIEW_UPLOAD", "User visited screening page"),
    )
    conn.commit()

    templates = conn.execute(
        "SELECT id, name, jd_text FROM jd_templates ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template("screening.html", templates=templates)


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
            return (
                jsonify({"ok": False, "error": "Minimum experience must be a number."}),
                400,
            )
        custom_weights = {
            "keyword": request.form.get("weight_keyword", 40),
            "semantic": request.form.get("weight_semantic", 35),
            "experience": request.form.get("weight_experience", 15),
            "achievements": request.form.get("weight_achievements", 10),
        }
        replace_existing = (
            request.form.get("replace_existing", "true").lower() == "true"
        )

        if not files:
            return jsonify({"ok": False, "error": "No files selected."}), 400
        if not jd_text:
            return (
                jsonify({"ok": False, "error": "Job description is required."}),
                400,
            )

        candidates, errors, jd_skills = process_files(
            files, jd_text, min_experience, custom_weights
        )
        if not candidates:
            return (
                jsonify(
                    {"ok": False, "error": "No valid resumes found.", "errors": errors}
                ),
                400,
            )

        conn = get_connection()
        # Save weight history
        conn.execute(
            """
            INSERT INTO weight_history (user_id, keyword_weight, semantic_weight, experience_weight, achievements_weight)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                custom_weights["keyword"],
                custom_weights["semantic"],
                custom_weights["experience"],
                custom_weights["achievements"],
            ),
        )
        if replace_existing:
            conn.execute("DELETE FROM candidates WHERE user_id = ?", (session["user_id"],))

        for c in candidates:
            conn.execute(
                """
                INSERT INTO candidates (
                    user_id, name, source_file, resume_text, extracted_skills, matched_skills, missing_skills,
                    years_experience, keyword_score, semantic_score, experience_score, final_score, rank, status,
                    ai_summary, ai_fit_score, tags, ai_explanation, strengths, weaknesses, rejection_reason,
                    ats_score, ats_formatting_issues, ats_keyword_coverage, ats_suggestions,
                    fraud_stuffing_detected, fraud_suspicious_claims, fraud_duplicate_content, fraud_authenticity_score,
                    success_interview_prob, success_hiring_prob, success_readiness_score,
                    questions_technical, questions_project, questions_behavioral, questions_hr,
                    education, certifications, achievements
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
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
                    c.get("ats_score", 0.0),
                    serialize_list(c.get("ats_formatting_issues")),
                    c.get("ats_keyword_coverage", 0.0),
                    serialize_list(c.get("ats_suggestions")),
                    c.get("fraud_stuffing_detected", 0),
                    serialize_list(c.get("fraud_suspicious_claims")),
                    c.get("fraud_duplicate_content", 0),
                    c.get("fraud_authenticity_score", 100.0),
                    c.get("success_interview_prob", 0.0),
                    c.get("success_hiring_prob", 0.0),
                    c.get("success_readiness_score", 0.0),
                    serialize_list(c.get("questions_technical")),
                    serialize_list(c.get("questions_project")),
                    serialize_list(c.get("questions_behavioral")),
                    serialize_list(c.get("questions_hr")),
                    serialize_list(c.get("education")),
                    serialize_list(c.get("certifications")),
                    serialize_list(c.get("achievements")),
                ),
            )
        conn.execute(
            "INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)",
            (session["user_id"], "BULK_SCREEN", f"Screened {len(candidates)} candidates successfully."),
        )
        conn.commit()
        conn.close()

        logger.info(
            "Screening completed: %d candidates processed, %d errors.",
            len(candidates),
            len(errors),
        )

        # Trigger alerts for top candidates
        if candidates and candidates[0]["final_score"] >= 85:
            top_c = candidates[0]
            job_title = jd_text[:50] + "..."
            send_slack_alert(top_c["name"], top_c["final_score"], job_title)
            hr_email = Config.HR_ALERT_EMAIL
            if hr_email:
                send_email_alert(
                    hr_email, top_c["name"], top_c["final_score"], job_title
                )

        return jsonify(
            {
                "ok": True,
                "processed": len(candidates),
                "errors": errors,
                "jd_skills": jd_skills,
                "top_candidate": candidates[0]["name"] if candidates else None,
            }
        )
    except Exception:
        logger.exception("Server error during screening.")
        return (
            jsonify({"ok": False, "error": "An internal server error occurred."}),
            500,
        )


@screening_bp.route("/dashboard")
@login_required
def dashboard():
    conn = get_connection()
    if session.get("role") == "Admin":
        rows = conn.execute(
            """
            SELECT id, name, source_file, resume_text, matched_skills, missing_skills,
                   keyword_score, semantic_score, experience_score, final_score, rank, status,
                   ai_summary, ai_fit_score, tags, ai_explanation, strengths, weaknesses, rejection_reason,
                   ats_score, ats_formatting_issues, ats_keyword_coverage, ats_suggestions,
                   fraud_stuffing_detected, fraud_suspicious_claims, fraud_duplicate_content, fraud_authenticity_score,
                   success_interview_prob, success_hiring_prob, success_readiness_score,
                   questions_technical, questions_project, questions_behavioral, questions_hr,
                   education, certifications, achievements
            FROM candidates
            ORDER BY rank ASC
            """
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, name, source_file, resume_text, matched_skills, missing_skills,
                   keyword_score, semantic_score, experience_score, final_score, rank, status,
                   ai_summary, ai_fit_score, tags, ai_explanation, strengths, weaknesses, rejection_reason,
                   ats_score, ats_formatting_issues, ats_keyword_coverage, ats_suggestions,
                   fraud_stuffing_detected, fraud_suspicious_claims, fraud_duplicate_content, fraud_authenticity_score,
                   success_interview_prob, success_hiring_prob, success_readiness_score,
                   questions_technical, questions_project, questions_behavioral, questions_hr,
                   education, certifications, achievements
            FROM candidates
            WHERE user_id = ?
            ORDER BY rank ASC
            """,
            (session["user_id"],)
        ).fetchall()
    
    activity_rows = conn.execute(
        """
        SELECT action, details, created_at FROM activity_logs 
        WHERE user_id = ? 
        ORDER BY created_at DESC LIMIT 5
        """,
        (session["user_id"],)
    ).fetchall()
    activity_logs = [dict(a) for a in activity_rows]
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
                "rejection_reason": row["rejection_reason"],
                "ats_score": row["ats_score"],
                "ats_formatting_issues": json.loads(row["ats_formatting_issues"] or "[]"),
                "ats_keyword_coverage": row["ats_keyword_coverage"],
                "ats_suggestions": json.loads(row["ats_suggestions"] or "[]"),
                "fraud_stuffing_detected": row["fraud_stuffing_detected"],
                "fraud_suspicious_claims": json.loads(row["fraud_suspicious_claims"] or "[]"),
                "fraud_duplicate_content": row["fraud_duplicate_content"],
                "fraud_authenticity_score": row["fraud_authenticity_score"],
                "success_interview_prob": row["success_interview_prob"],
                "success_hiring_prob": row["success_hiring_prob"],
                "success_readiness_score": row["success_readiness_score"],
                "questions_technical": json.loads(row["questions_technical"] or "[]"),
                "questions_project": json.loads(row["questions_project"] or "[]"),
                "questions_behavioral": json.loads(row["questions_behavioral"] or "[]"),
                "questions_hr": json.loads(row["questions_hr"] or "[]"),
                "education": json.loads(row["education"] or "[]"),
                "certifications": json.loads(row["certifications"] or "[]"),
                "achievements": json.loads(row["achievements"] or "[]"),
            }
        )

    return render_template(
        "dashboard.html",
        candidates=candidates,
        skill_frequency=skill_frequency,
        activity_logs=activity_logs
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
        headers={
            "Content-Disposition": "attachment; filename=resume_upload_template.csv"
        },
    )


@screening_bp.route("/api/weights/history")
@login_required
def get_weight_history():
    conn = get_connection()
    history = conn.execute(
        "SELECT keyword_weight, semantic_weight, experience_weight, achievements_weight, created_at "
        "FROM weight_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "history": [dict(h) for h in history]})


@screening_bp.route("/api/weights/suggest")
@login_required
def suggest_weights():
    suggestions = {
        "Tech-heavy": {
            "keyword": 40,
            "semantic": 40,
            "experience": 10,
            "achievements": 10,
        },
        "Managerial": {
            "keyword": 20,
            "semantic": 30,
            "experience": 30,
            "achievements": 20,
        },
        "Internship": {
            "keyword": 50,
            "semantic": 30,
            "experience": 5,
            "achievements": 15,
        },
    }
    return jsonify({"ok": True, "suggestions": suggestions})


@screening_bp.route("/api/skill-gap/<int:candidate_id>")
@login_required
def get_skill_gap(candidate_id):
    conn = get_connection()
    if session.get("role") == "Admin":
        row = conn.execute(
            "SELECT matched_skills, missing_skills FROM candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT matched_skills, missing_skills FROM candidates WHERE id = ? AND user_id = ?",
            (candidate_id, session["user_id"]),
        ).fetchone()
    conn.close()
    if not row:
        return jsonify({"ok": False, "error": "Candidate not found"}), 404
    return jsonify(
        {
            "ok": True,
            "matched": json.loads(row["matched_skills"] or "[]"),
            "missing": json.loads(row["missing_skills"] or "[]"),
        }
    )


@screening_bp.route("/update-status/<int:candidate_id>", methods=["POST"])
@login_required
def update_status(candidate_id):
    status = request.form.get("status", "Pending")
    if status not in VALID_STATUSES:
        return jsonify({"ok": False, "error": "Invalid status"}), 400

    conn = get_connection()
    if session.get("role") == "Admin":
        conn.execute(
            "UPDATE candidates SET status = ? WHERE id = ?", (status, candidate_id)
        )
    else:
        conn.execute(
            "UPDATE candidates SET status = ? WHERE id = ? AND user_id = ?",
            (status, candidate_id, session["user_id"]),
        )
    conn.commit()
    conn.close()
    logger.info("Candidate %d status updated to '%s'.", candidate_id, status)
    return jsonify({"ok": True})


@screening_bp.route("/export/excel")
@login_required
def export_excel():
    conn = get_connection()
    if session.get("role") == "Admin":
        rows = conn.execute(
            "SELECT name, source_file, keyword_score, semantic_score, experience_score, "
            "final_score, rank, status FROM candidates ORDER BY rank ASC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT name, source_file, keyword_score, semantic_score, experience_score, "
            "final_score, rank, status FROM candidates WHERE user_id = ? ORDER BY rank ASC",
            (session["user_id"],)
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
    if session.get("role") == "Admin":
        rows = conn.execute(
            """
            SELECT rank, name, final_score, status, ats_score, ai_summary, 
                   matched_skills, missing_skills, strengths, weaknesses,
                   questions_technical, questions_project, questions_behavioral, questions_hr
            FROM candidates ORDER BY rank ASC
            """
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT rank, name, final_score, status, ats_score, ai_summary, 
                   matched_skills, missing_skills, strengths, weaknesses,
                   questions_technical, questions_project, questions_behavioral, questions_hr
            FROM candidates WHERE user_id = ? ORDER BY rank ASC
            """,
            (session["user_id"],)
        ).fetchall()
    conn.close()

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        output = io.BytesIO()
        pdf = canvas.Canvas(output, pagesize=A4)
        
        for index, r in enumerate(rows):
            if index > 0:
                pdf.showPage()
                
            y = 800
            # Header
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(40, y, "HIREMIND AI - CANDIDATE REPORT")
            pdf.setStrokeColorRGB(0.48, 0.22, 0.92) # Purple
            pdf.setLineWidth(2)
            pdf.line(40, y-10, 550, y-10)
            
            y -= 40
            # Candidate Info
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(40, y, f"{r['name']} (Rank #{r['rank']})")
            
            y -= 25
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(40, y, f"Match Score: {r['final_score']}%  |  ATS Score: {r['ats_score']}%  |  Status: {r['status']}")
            
            y -= 30
            # AI Summary
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(40, y, "Candidate Summary:")
            pdf.setFont("Helvetica", 9.5)
            summary = r['ai_summary'] or "No summary available."
            # Wrap text
            words = summary.split()
            lines = []
            current_line = []
            for w in words:
                current_line.append(w)
                if len(" ".join(current_line)) > 90:
                    current_line.pop()
                    lines.append(" ".join(current_line))
                    current_line = [w]
            if current_line:
                lines.append(" ".join(current_line))
                
            for line in lines[:4]:
                y -= 15
                pdf.drawString(45, y, line)
                
            y -= 25
            # Strengths & Weaknesses
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(40, y, "Strengths & Gaps:")
            
            y -= 15
            pdf.setFont("Helvetica-Bold", 9.5)
            pdf.drawString(45, y, "Strengths:")
            pdf.setFont("Helvetica", 9)
            strengths_list = json.loads(r['strengths'] or "[]")
            for s in strengths_list[:3]:
                y -= 14
                pdf.drawString(55, y, f"- {s}")
                
            y -= 18
            pdf.setFont("Helvetica-Bold", 9.5)
            pdf.drawString(45, y, "Gaps & Weaknesses:")
            pdf.setFont("Helvetica", 9)
            weaknesses_list = json.loads(r['weaknesses'] or "[]")
            for w in weaknesses_list[:3]:
                y -= 14
                pdf.drawString(55, y, f"- {w}")

            y -= 25
            # Skill Gap
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(40, y, "Skills Fit:")
            pdf.setFont("Helvetica", 9)
            matched = json.loads(r['matched_skills'] or "[]")
            missing = json.loads(r['missing_skills'] or "[]")
            y -= 15
            pdf.drawString(45, y, f"Matched Skills: {', '.join(matched[:8])}")
            y -= 15
            pdf.drawString(45, y, f"Missing Skills: {', '.join(missing[:8]) if missing else 'None'}")

            y -= 25
            # Interview Questions
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(40, y, "Selected Interview Questions:")
            pdf.setFont("Helvetica", 9)
            
            tech_q = json.loads(r['questions_technical'] or "[]")
            proj_q = json.loads(r['questions_project'] or "[]")
            behav_q = json.loads(r['questions_behavioral'] or "[]")
            hr_q = json.loads(r['questions_hr'] or "[]")
            
            questions = []
            if tech_q: questions.append(f"Technical: {tech_q[0]}")
            if proj_q: questions.append(f"System/Project: {proj_q[0]}")
            if behav_q: questions.append(f"Behavioral: {behav_q[0]}")
            if hr_q: questions.append(f"HR Fit: {hr_q[0]}")
            
            for q in questions[:4]:
                y -= 15
                pdf.drawString(45, y, q[:110])
                if len(q) > 110:
                    y -= 12
                    pdf.drawString(55, y, q[110:220])
                    
            pdf.setFont("Helvetica", 8)
            pdf.drawString(40, 30, f"Page {index + 1} of {len(rows)} | Generated by HireMind AI")
            
        pdf.save()
        output.seek(0)
        payload = output.getvalue()
    except Exception:
        logger.exception("PDF generation failed.")
        payload = b"An error occurred generating the PDF report."

    return Response(
        payload,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=candidates-report.pdf"},
    )


@screening_bp.route("/api/ai/chat", methods=["POST"])
@login_required
def ai_chat():
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"ok": False, "error": "Message is empty"}), 400
    
    conn = get_connection()
    if session.get("role") == "Admin":
        rows = conn.execute(
            """
            SELECT name, source_file, resume_text, matched_skills, missing_skills,
                   years_experience, final_score, rank, status, ai_summary, strengths, weaknesses,
                   education, certifications, achievements
            FROM candidates
            ORDER BY rank ASC
            """
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT name, source_file, resume_text, matched_skills, missing_skills,
                   years_experience, final_score, rank, status, ai_summary, strengths, weaknesses,
                   education, certifications, achievements
            FROM candidates
            WHERE user_id = ?
            ORDER BY rank ASC
            """,
            (session["user_id"],)
        ).fetchall()
    conn.close()
    
    candidates = []
    all_skills = set()
    all_missing_skills = set()
    for row in rows:
        matched = json.loads(row["matched_skills"] or "[]")
        missing = json.loads(row["missing_skills"] or "[]")
        for s in matched:
            all_skills.add(s)
        for s in missing:
            all_missing_skills.add(s)
        candidates.append({
            "name": row["name"],
            "source_file": row["source_file"],
            "matched_skills": matched,
            "missing_skills": missing,
            "years_experience": row["years_experience"],
            "final_score": row["final_score"],
            "rank": row["rank"],
            "status": row["status"],
            "ai_summary": row["ai_summary"],
            "strengths": json.loads(row["strengths"] or "[]"),
            "weaknesses": json.loads(row["weaknesses"] or "[]"),
            "education": json.loads(row["education"] or "[]"),
            "certifications": json.loads(row["certifications"] or "[]"),
            "achievements": json.loads(row["achievements"] or "[]"),
        })
        
    response = ""
    msg = message.lower()
    
    # 0. Check if this is Resume Q&A about a specific candidate
    found_cand = None
    for c in candidates:
        if c["name"].lower() in msg or (f"candidate {c['rank']}" in msg) or (f"candidate {c['name'].lower()}" in msg):
            found_cand = c
            break
            
    if found_cand:
        if "project" in msg or "build" in msg or "achieve" in msg or "accomplish" in msg:
            proj_list = found_cand["achievements"]
            if proj_list:
                response = f"Here are the key projects and achievements for **{found_cand['name']}**:\n" + "\n".join([f"- {p}" for p in proj_list[:4]])
            else:
                response = f"**{found_cand['name']}** does not explicitly list distinct quantifiable achievements or project metrics in their resume, but their experience includes: {found_cand['ai_summary']}."
        elif "certification" in msg or "certif" in msg or "credential" in msg:
            certs = found_cand["certifications"]
            if certs:
                response = f"**{found_cand['name']}** holds the following certifications:\n" + "\n".join([f"- {crt}" for crt in certs])
            else:
                response = f"No specific certifications were found for **{found_cand['name']}**."
        elif "education" in msg or "degree" in msg or "college" in msg or "university" in msg:
            edu = found_cand["education"]
            if edu:
                response = f"Education history for **{found_cand['name']}**:\n" + "\n".join([f"- {e}" for e in edu])
            else:
                response = f"No structured education history parsed for **{found_cand['name']}**."
        elif "skill" in msg:
            response = (
                f"Skills analysis for **{found_cand['name']}**:\n"
                f"- **Matched Skills**: {', '.join(found_cand['matched_skills']) if found_cand['matched_skills'] else 'None'}\n"
                f"- **Missing Skills**: {', '.join(found_cand['missing_skills']) if found_cand['missing_skills'] else 'None'}"
            )
        elif "know" in msg or "has" in msg or "experience with" in msg:
            # Check if candidate knows a specific technology
            tech_match = None
            for s in (list(all_skills) + list(all_missing_skills)):
                if s.lower() in msg:
                    tech_match = s
                    break
            if tech_match:
                if tech_match in found_cand["matched_skills"]:
                    response = f"Yes, **{found_cand['name']}** has verified experience with **{tech_match}** based on their resume profile."
                else:
                    response = f"No, **{found_cand['name']}** does not appear to list **{tech_match}** on their resume."
            else:
                response = f"Could you specify which skill or technology you want to verify for **{found_cand['name']}**?"
        else:
            status_text = "Shortlisted" if found_cand['status'] == 'Selected' else "Rejected" if found_cand['status'] == 'Rejected' else "Under Review"
            response = (
                f"### Profile Summary for **{found_cand['name']}** (Rank #{found_cand['rank']})\n"
                f"- **Final Match Score**: {found_cand['final_score']}%\n"
                f"- **Total Experience**: {found_cand['years_experience']} years\n"
                f"- **Status**: {status_text}\n"
                f"- **Overview**: {found_cand['ai_summary']}\n\n"
                f"**Key Strengths**:\n" + "\n".join([f"- {s}" for s in found_cand['strengths'][:3]]) + "\n\n"
                f"**Skill Gaps**:\n" + "\n".join([f"- {w}" for w in found_cand['weaknesses'][:3]])
            )

    # 1. Natural Language Search: Experience Filter (e.g. "Find candidates with 2+ years experience")
    elif "year" in msg or "experience" in msg or "exp" in msg:
        match_years = re.search(r"(\d+)\+?\s*years?", msg)
        if match_years:
            min_y = float(match_years.group(1))
            matching = [c for c in candidates if c["years_experience"] >= min_y]
            if matching:
                response = f"I found **{len(matching)}** candidates with **{min_y}+ years** of experience:\n"
                response += "\n".join([f"- **{c['name']}** (Rank #{c['rank']}, {c['years_experience']} yrs, Score {c['final_score']}%): {c['ai_summary']}" for c in matching[:5]])
            else:
                response = f"No candidates found with at least {min_y} years of experience."
        else:
            # Check for average experience or general stats
            if "average" in msg or "mean" in msg:
                avg_score = round(sum(c["final_score"] for c in candidates) / len(candidates), 1) if candidates else 0
                avg_exp = round(sum(c["years_experience"] for c in candidates) / len(candidates), 1) if candidates else 0
                response = f"The talent pool has an average experience of **{avg_exp} years** and an average match score of **{avg_score}%** across {len(candidates)} candidates."
            else:
                response = "I can search candidates by experience. Try asking: *'Find candidates with 3+ years experience'*."

    # 2. Natural Language Search: Skills Filter (e.g. "Find candidates with NLP skills")
    elif any(s.lower() in msg for s in all_skills) or any(s.lower() in msg for s in all_missing_skills):
        target_skill = None
        for s in (list(all_skills) + list(all_missing_skills)):
            if s.lower() in msg:
                target_skill = s
                break
        
        matching = [c for c in candidates if target_skill in c["matched_skills"]]
        if matching:
            response = f"I found **{len(matching)}** candidates matching **{target_skill}**:\n"
            response += "\n".join([f"- **{c['name']}** (Rank #{c['rank']}, Score {c['final_score']}%): {c['years_experience']} yrs exp | {c['ai_summary']}" for c in matching[:5]])
        else:
            response = f"No candidates in this pool currently match the skill: **{target_skill}**."

    # 3. Natural Language Search: Rank Filters (e.g. "Show top ranked candidates")
    elif "top" in msg or "best" in msg or "highest" in msg or "rank" in msg:
        if not candidates:
            response = "No candidates are in the database yet. Please screen resumes first."
        else:
            top_cand = candidates[0]
            response = (
                f"The top-ranked candidate is **{top_cand['name']}** (Rank #1) with an overall AI score of **{top_cand['final_score']}%** and {top_cand['years_experience']} years of experience.\n\n"
                f"**AI Summary**: {top_cand['ai_summary']}\n"
            )
            if len(candidates) > 1:
                response += f"\nOther highly-ranked candidates include:\n" + "\n".join([f"- **{c['name']}** (Rank #{c['rank']}, Score {c['final_score']}%): {c['years_experience']} yrs exp" for c in candidates[1:4]])

    # 4. General Info about HireMind AI
    elif "hiremind" in msg and ("what" in msg or "about" in msg or "info" in msg or "tell me" in msg or "who" in msg or "help" in msg or msg.strip() == "hiremind"):
        response = (
            "**HireMind AI** is an intelligent, enterprise-grade resume screening and recruitment platform.\n\n"
            "Key features include:\n"
            "- **ATS Compatibility Checker**: Scans resume styling, format compatibility, and keyword density.\n"
            "- **Fraud & Stuffing Detector**: Identifies duplicate paragraphs and suspicious timeline claims.\n"
            "- **Candidate Success Gauges**: Predicts interview conversion probabilities and overall readiness.\n"
            "- **Dynamic Interview Generator**: Creates candidate-tailored technical, system, behavioral, and HR questions."
        )

    # 5. Fallback general help instructions
    else:
        response = (
            "I'm here to search the talent pool and answer details about resumes! Try asking:\n"
            "- **Skills search**: *'Show candidates with Python'*, *'Who knows React?'*\n"
            "- **Experience search**: *'Find candidates with 2+ years experience'*\n"
            "- **Resume Q&A**: *'What projects did John Doe build?'*, *'Does Candidate 1 have AWS certifications?'*, *'Summarize education for Jane Smith'*.\n"
            "- **Top candidates**: *'Show top ranked candidates'*, *'Who is the best match?'*"
        )
            
    return jsonify({"ok": True, "response": response})
