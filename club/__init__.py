"""Flask application setup."""
import os
import secrets
from datetime import timedelta
from flask import Flask

from .config import BASE_DIR


def create_app(config=None):
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    # Keep a stable signing key across restarts without checking it into git.
    key_path = BASE_DIR / "submissions" / ".session-key"
    key_path.parent.mkdir(exist_ok=True)
    if not key_path.exists():
        try:
            with key_path.open("x", encoding="utf-8") as handle:
                handle.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY") or key_path.read_text().strip(),
                      ATTEMPT_DATABASE=BASE_DIR / "submissions" / "attempts.sqlite3",
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict",
                      PERMANENT_SESSION_LIFETIME=timedelta(days=3650),
                      SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
                      MAX_CONTENT_LENGTH=1024 * 1024,
                      ALLOW_UNSAFE_REMOTE_EXECUTION=False)
    if config:
        app.config.update(config)
    from .routes import pages
    app.register_blueprint(pages)
    from .admin import register_commands
    register_commands(app)
    return app
