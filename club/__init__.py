"""Flask application setup."""
import os
import re
import secrets
from datetime import timedelta
from flask import Flask

from .config import APP_URL_PREFIX, BASE_DIR


def create_app(config=None):
    settings = dict(config or {})
    prefix = settings.get("APP_URL_PREFIX", os.environ.get("APP_URL_PREFIX", APP_URL_PREFIX))
    if not isinstance(prefix, str):
        raise ValueError("APP_URL_PREFIX must be a URL path string")
    prefix = "/" + prefix.strip("/") if prefix.strip("/") else ""
    if not re.fullmatch(r"(?:/[A-Za-z0-9._~-]+)*", prefix) or any(
        part in (".", "..") for part in prefix.split("/")
    ):
        raise ValueError("APP_URL_PREFIX must be a path such as /tryouts, or empty for root")
    settings["APP_URL_PREFIX"] = prefix
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
        static_url_path=prefix + "/static",
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
                      SESSION_COOKIE_PATH=prefix or "/",
                      PERMANENT_SESSION_LIFETIME=timedelta(days=3650),
                      SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
                      MAX_CONTENT_LENGTH=1024 * 1024,
                      ALLOW_UNSAFE_REMOTE_EXECUTION=False)
    app.config.update(settings)
    from .routes import pages
    app.register_blueprint(pages, url_prefix=prefix)
    from .admin import register_commands
    register_commands(app)
    return app
