from flask import Blueprint, request, jsonify, abort
from sqlalchemy import func
from .models import CleanRecipe, IngredientAllergen
from . import db

api_bp = Blueprint("api", __name__, url_prefix="/api")

# --- constants ----------------------------------------------------------
ALLERGENS = [
    "Gluten","Milk","Egg","Fish","Crustaceans","Molluscs","Tree Nuts",
    "Peanuts","Soy","Sesame","Celery","Mustard","Lupin","Sulphites"
]
# ------------------------------------------------------------------------

@api_bp.route("/allergens", methods=["GET"])
def list_allergens():
    """Return the canonical list of 14 allergen categories."""
    return jsonify(ALLERGENS)


@api_bp.route("/recipes", methods=["GET"])
def filtered_recipes():
    """
    Query params:
        exclude=Milk&exclude=Egg  (repeatable)   – allergens to REMOVE
        q=keyword                 – optional search string
        limit=20                  – optional cap
    """
    try:
        exclude = request.args.getlist("exclude") or []
        exclude = [e.strip() for e in exclude if e.strip()]

        q       = request.args.get("q", "").strip()
        limit   = int(request.args.get("limit", 20))
    except (ValueError, TypeError):
        abort(400, "Bad query parameters")

    # Sub-query: recipes that contain ANY of the excluded allergens
    if exclude:
        sub = (
            db.session.query(IngredientAllergen.recipe_id)
            .filter(IngredientAllergen.allergen.in_(exclude))
            .subquery()
        )
        base = CleanRecipe.query.filter(~CleanRecipe.id.in_(sub))
    else:
        base = CleanRecipe.query

    if q:
        base = base.filter(CleanRecipe.recipe_title.ilike(f"%{q}%"))

    rows = (
        base
        .order_by(func.random())      
        .limit(limit)
        .all()
    )

    data = [
        {
            "id": r.id,
            "title": r.recipe_title,
            "tags": (r.tags or "").split(","),
            "allergens": sorted({a.allergen for a in r.allergens})
        }
        for r in rows
    ]
    return jsonify(data)


@api_bp.route("/recipe/<int:recipe_id>", methods=["GET"])
def recipe_detail(recipe_id):
    r = CleanRecipe.query.get_or_404(recipe_id)
    return jsonify(
        id          = r.id,
        title       = r.recipe_title,
        ingredients = r.ingredients.splitlines(),
        instructions= r.instructions.splitlines(),
        tags        = (r.tags or "").split(","),
        allergens   = sorted({a.allergen for a in r.allergens})
    )
