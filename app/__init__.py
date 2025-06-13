"""
Flask factory + SQLAlchemy setup
"""

import os, secrets
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

db   = SQLAlchemy()
csrf = CSRFProtect()                     


def create_app() -> Flask:
    app = Flask(__name__,
                static_folder="../static",
                template_folder="../templates")

    db_uri = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:admin@localhost:5432/allergen_recipes",
    ).replace("postgres://", "postgresql://", 1)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.getenv("SECRET_KEY", secrets.token_hex(16)),
    )

    db.init_app(app)

    UI_ORIGINS = {
        "https://allergen-recipe-filter.onrender.com",
        "http://127.0.0.1:5000",
    }
    CORS(app, origins=UI_ORIGINS)

    csrf.init_app(app)                   
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    @app.after_request
    def add_security_headers(resp):      
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

    from .routes import api_bp           
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    print("→ DB HOST =", db_uri.split("@")[-1].split("/")[0])
    return app
