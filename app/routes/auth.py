import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.services.database import get_connection

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_connection()
        user = conn.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            # Log activity
            conn.execute(
                "INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)",
                (user["id"], "LOGIN", f"User {username} logged in"),
            )
            conn.commit()
            conn.close()

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            logger.info("User '%s' logged in successfully.", username)
            flash("Welcome back.", "success")
            return redirect(url_for("screening.index"))

        conn.close()
        logger.warning("Failed login attempt for username: '%s'", username)
        flash("Invalid username or password.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if len(username) < 3 or len(password) < 6:
        flash("Username (min 3 chars) or password (min 6 chars) too short.", "warning")
        return redirect(url_for("auth.login"))

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        conn.commit()
        logger.info("New user registered: '%s'", username)
    except Exception:
        logger.warning("Registration failed — username '%s' may already exist.", username)
        flash("Username already exists.", "warning")
        conn.close()
        return redirect(url_for("auth.login"))
    conn.close()
    flash("Registration successful. Please login.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
def logout():
    username = session.get("username", "unknown")
    session.clear()
    logger.info("User '%s' logged out.", username)
    flash("Logged out securely.", "info")
    return redirect(url_for("auth.login"))
