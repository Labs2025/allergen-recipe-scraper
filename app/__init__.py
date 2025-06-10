"""
Flask factory + SQLAlchemy setup.

  • Locally (uses localhost URI if DATABASE_URL is absent)
  • On Render   (DATABASE_URL is injected in Environment)
"""

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os  

db = SQLAlchemy()


def create_app() -> Flask:
    """Application factory called by gunicorn / flask run."""

    # ------------------------------------------------------------------
    # 1) Initialise Flask 
    # ------------------------------------------------------------------
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates",
    )

    # ------------------------------------------------------------------
    # 2) Choose the database connection string
    # ------------------------------------------------------------------
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        # Local default
        db_url = "postgresql://postgres:admin@localhost:5432/allergen_recipes"
    else:
        # Render sometimes sends URLs starting with “postgres://”
        # SQLAlchemy expects “postgresql://”
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Log the URI host for quick debugging 
    print("→ DB HOST =", db_url.split("@")[-1].split("/")[0])

    # ------------------------------------------------------------------
    # 3) Extensions & blueprints
    # ------------------------------------------------------------------
    db.init_app(app)
    CORS(app)

    # API routes
    from .routes import api_bp  # local import to avoid circular refs
    app.register_blueprint(api_bp)

    # Root HTML page
    @app.route("/")
    def index():
        return render_template("index.html")

    return app
