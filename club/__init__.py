"""Flask application setup."""
from flask import Flask

from .config import BASE_DIR


def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    from .routes import pages
    app.register_blueprint(pages)
    return app
