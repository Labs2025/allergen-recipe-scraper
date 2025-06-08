from flask import Flask, render_template              # ← add render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    # ---------------------------------------------------
    # adjust the paths only if you changed the layout
    # ---------------------------------------------------
    app = Flask(
        __name__,
        static_folder="../static",          # points to …/static
        template_folder="../templates"      # points to …/templates
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql://postgres:admin@localhost:5432/allergen_recipes"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    CORS(app)

    # --- API blueprint (already there) -----------------
    from .routes import api_bp
    app.register_blueprint(api_bp)

    # === NEW: root page  ===============================
    @app.route("/")
    def index():
        # renders templates/index.html
        return render_template("index.html")
    # ===================================================

    return app
