"""
API routes with basic input validation, XSS-safe output,
CSRF-failure demo endpoint and tight CORS behaviour.
"""

import html
from flask import Blueprint, request, jsonify, abort
from flask_wtf.csrf import validate_csrf
from sqlalchemy import func
from .models import CleanRecipe, IngredientAllergen
from . import db, csrf

api_bp = Blueprint("api", __name__, url_prefix="/api")

ALLERGENS = [
    "Gluten", "Milk", "Egg", "Fish", "Crustaceans", "Molluscs",
    "Tree Nuts", "Peanuts", "Soy", "Sesame",
    "Celery", "Mustard", "Lupin", "Sulphites",
]


def safe(text: str) -> str:
    return (
        text.replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
    )


@api_bp.route("/allergens", methods=["GET"])
def list_allergens():
    """Return the allergen categories."""
    return jsonify(ALLERGENS)


@api_bp.route("/recipes", methods=["GET"])
def filtered_recipes():
    """
    GET params
    ----------
    exclude=Milk&exclude=Egg   allergens to remove
    q=keyword                  free-text search
    limit=20                   1-50
    """
    exclude_raw = request.args.getlist("exclude") or []
    q_raw        = request.args.get("q", "").strip()

    try:
        limit = int(request.args.get("limit", 20))
    except ValueError:
        abort(400, "limit must be an integer")

    invalid = [x for x in exclude_raw if x not in ALLERGENS]
    if invalid:
        abort(400, f"Unknown allergen(s): {', '.join(invalid)}")

    exclude = exclude_raw
    limit   = max(1, min(limit, 50))
    q       = q_raw[:120]                       

    qry = CleanRecipe.query
    if exclude:
        sub = (
            db.session.query(IngredientAllergen.recipe_id)
            .filter(IngredientAllergen.allergen.in_(exclude))
            .subquery()
        )
        qry = qry.filter(~CleanRecipe.id.in_(sub))

    if q:
        qry = qry.filter(CleanRecipe.recipe_title.ilike(f"%{q}%"))

    rows = qry.order_by(func.random()).limit(limit).all()

    return jsonify([
        {
            "id": r.id,
            "title": safe(r.recipe_title),
            "tags": [safe(t) for t in (r.tags or "").split(",") if t],
            "allergens": sorted({a.allergen for a in r.allergens}),
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


# -----------------------------------------------------------------
# 🔒 Test-only endpoint: must reject if CSRF token missing
# -----------------------------------------------------------------
@api_bp.route("/secure-post", methods=["POST"])
def secure_post():
    token = (
        request.headers.get("X-CSRFToken")
        or request.form.get("csrf_token")
        or request.json.get("csrf_token") if request.is_json else None
    )
    if not token:
        abort(400, "Missing CSRF token")

    try:
        validate_csrf(token)
    except Exception:      
        abort(403, "Invalid CSRF token")

    # If the token is valid we simply acknowledge success.
    return jsonify(ok=True), 200
