from flask import Flask, jsonify, redirect, request, url_for

from config import Config
from routes.auth import auth_bp
from routes.screening import screening_bp
from services.database import init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    init_db()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(screening_bp)

    # Handle large file uploads
    @app.errorhandler(413)
    def request_entity_too_large(_error):
        if request.path.startswith("/api/"):
            size_mb = app.config.get("MAX_CONTENT_LENGTH", 0) // (1024 * 1024)
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": f"Upload too large. Max allowed size is {size_mb} MB per request. Upload fewer files or smaller files.",
                    }
                ),
                413,
            )
        return redirect(url_for("screening.index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)