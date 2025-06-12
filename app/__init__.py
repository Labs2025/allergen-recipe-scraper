"""
Flask factory + SQLAlchemy setup
────────────────────────────────
• Locally  → falls back to localhost DB URI
• Render   → uses DATABASE_URL injected in the env
• Adds     → CORS, CSRF, security headers
"""

import os, secrets
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

db   = SQLAlchemy()
csrf = CSRFProtect()                     # enables CSRF for future POST/PUT/PATCH/DELETE


def create_app() -> Flask:
    # -------------------------------------------------------------- 1) build
    app = Flask(__name__,
                static_folder="../static",
                template_folder="../templates")

    # -------------------------------------------------------------- 2) DB URI
    db_uri = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:admin@localhost:5432/allergen_recipes",
    ).replace("postgres://", "postgresql://", 1)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.getenv("SECRET_KEY", secrets.token_hex(16)),
    )

    # -------------------------------------------------------------- 3) ext
    db.init_app(app)

    # CORS – _allow only your own front-end origins_
    UI_ORIGINS = {
        "https://allergen-recipe-filter.onrender.com",
        "http://127.0.0.1:5000",
    }
    # `origins` alone is enough – don’t rely on the nested syntax
    CORS(app, origins=UI_ORIGINS)

    csrf.init_app(app)                   # CSRF protection
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # -------------------------------------------------------------- 4) headers
    @app.after_request
    def add_security_headers(resp):      # noqa: D401
        resp.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data: https:; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src  'self' https://cdn.jsdelivr.net 'unsafe-inline';"
        )
        return resp

    # -------------------------------------------------------------- 5) blueprints & root
    from .routes import api_bp           # late import avoids circular refs
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    # helpful in Render logs
    print("→ DB HOST =", db_uri.split("@")[-1].split("/")[0])
    return app
