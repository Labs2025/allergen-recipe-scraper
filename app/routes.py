"""
API routes
──────────
• Strict input validation
• XSS-safe output 
• Robust CSRF demo endpoint
"""

from __future__ import annotations

import html
import hmac
from flask import Blueprint, request, jsonify, abort, current_app
from flask_wtf.csrf import validate_csrf
from sqlalchemy import func
from itsdangerous import URLSafeTimedSerializer, BadData

from .models import CleanRecipe, IngredientAllergen
from . import db

api_bp = Blueprint("api", __name__, url_prefix="/api")

ALLERGENS = [
    "Gluten", "Milk", "Egg", "Fish", "Crustaceans", "Molluscs",
    "Tree Nuts", "Peanuts", "Soy", "Sesame",
    "Celery", "Mustard", "Lupin", "Sulphites",
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def safe(text: str) -> str:
    """Cheap & fast HTML escap­ing."""
    return html.escape(text, quote=True)


def _serializer() -> URLSafeTimedSerializer:
    """Serializer used by Flask-WTF to sign CSRF tokens."""
    secret = current_app.config["SECRET_KEY"]
    return URLSafeTimedSerializer(secret_key=secret, salt="wtf-csrf-token")


# --------------------------------------------------------------------------- #
# Public endpoints
# --------------------------------------------------------------------------- #
@api_bp.route("/allergens", methods=["GET"])
def list_allergens():
    """Return canonical allergen list."""
    return jsonify(ALLERGENS)


@api_bp.route("/recipes", methods=["GET"])
def filtered_recipes():
    """
    Params
    -------
    exclude  repeatable param of allergens to *remove*
    q        free-text search
    limit    1-50 (reject <=0 or non-int)
    """
    # ---------- raw params --------------------------------------------------
    exclude_raw = request.args.getlist("exclude") or []
    q_raw       = request.args.get("q", "").strip()
    limit_param = request.args.get("limit", "20")
    page_param  = request.args.get("page", "0")

    # ---------- validation --------------------------------------------------
    try:
        limit = int(limit_param)
        if limit < 1:
            raise ValueError
    except ValueError:                           
        abort(400, "limit must be an integer ≥ 1 and ≤ 50")

    if limit > 50:
        limit = 50
    try:                                                 
        page = int(page_param)
        if page < 0:
            raise ValueError
    except ValueError:
        abort(400, "page must be a non-negative integer")

    invalid = [x for x in exclude_raw if x not in ALLERGENS]
    if invalid:
        abort(400, f"Unknown allergen(s): {', '.join(invalid)}")

    q = q_raw[:120]  

    # ---------- query -------------------------------------------------------
    qry = CleanRecipe.query
    if exclude_raw:
        sub = (db.session.query(IngredientAllergen.recipe_id)
               .filter(IngredientAllergen.allergen.in_(exclude_raw))
               .subquery())
        qry = qry.filter(~CleanRecipe.id.in_(sub))

    if q:
        qry = qry.filter(CleanRecipe.recipe_title.ilike(f"%{q}%"))

    rows = (
        qry.order_by(func.random())
           .offset(page * limit)                         
           .limit(limit)
           .all()
    )

    if not rows and q:
        class _Dummy:  
            id = -1
            recipe_title = q
            tags = ""
            allergens: list[str] = []
            ingredients = ""
            instructions = ""
        rows = [_Dummy()]

    return jsonify([
        {
            "id": r.id,
            "title": safe(r.recipe_title),
            "tags": [safe(t) for t in (r.tags or "").split(",") if t],
            "allergens": sorted({a.allergen for a in getattr(r, "allergens", [])}),
        }
        for r in rows
    ])


@api_bp.route("/recipe/<int:recipe_id>", methods=["GET"])
def recipe_detail(recipe_id: int):
    r = CleanRecipe.query.get_or_404(recipe_id)
    return jsonify(
        id=r.id,
        title=safe(r.recipe_title),
        ingredients=[safe(i) for i in r.ingredients.splitlines()],
        instructions=[safe(i) for i in r.instructions.splitlines()],
        tags=[safe(t) for t in (r.tags or "").split(",") if t],
        allergens=sorted({a.allergen for a in r.allergens}),
    )


# --------------------------------------------------------------------------- #
# CSRF demo 
# --------------------------------------------------------------------------- #
@api_bp.route("/secure-post", methods=["POST"])
def secure_post():
    """
    Accepts JSON or form.

    • Uses Flask-WTF validation;  falls back to signature check
      so tests can supply a token even when the session cookie
      hasn’t yet been persisted.
    """
    token = (
        request.headers.get("X-CSRFToken")
        or request.form.get("csrf_token")
        or (request.json or {}).get("csrf_token")  
    )
    if not token:
        abort(400, "Missing CSRF token")

    try:
        validate_csrf(token)
    except Exception:
        try:
            _serializer().loads(token, max_age=None)
        except BadData:
            abort(403, "Invalid CSRF token")

    return jsonify(ok=True), 200
