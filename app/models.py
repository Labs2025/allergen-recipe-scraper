from . import db

class CleanRecipe(db.Model):
    __tablename__ = "clean_recipes"
    id           = db.Column(db.Integer, primary_key=True)
    recipe_title = db.Column(db.Text,  nullable=False)
    ingredients  = db.Column(db.Text,  nullable=False)
    instructions = db.Column(db.Text,  nullable=False)
    tags         = db.Column(db.Text)

class IngredientAllergen(db.Model):
    __tablename__ = "ingredient_allergens"
    id          = db.Column(db.Integer, primary_key=True)
    recipe_id   = db.Column(db.Integer, db.ForeignKey("clean_recipes.id"))
    allergen    = db.Column(db.Text,   nullable=False)

    recipe      = db.relationship("CleanRecipe", backref="allergens")
