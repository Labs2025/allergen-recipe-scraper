#!/usr/bin/env python

import os
import re
import psycopg2

# ----------------------------------------------------------------------
DB_URL = "postgresql://postgres:admin@localhost:5432/allergen_recipes"
# ----------------------------------------------------------------------

def normalize_ingredient(raw_text):
    text = raw_text.lower()
    text = re.sub(r"\(.*?\)", " ", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    units_pattern = r"\b\d+\b|\b(?:cup|cups|tbsp|tsp|tablespoon|teaspoon|gram|grams|g|kg|oz|ounce|ounces|ml|liter|litre|l)\b"
    text = re.sub(units_pattern, "", text)
    return text.strip()

def main():
    print(f"Connecting to DB: {DB_URL}")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # <<< Fixed TRUNCATE syntax here >>>
    print("[INFO] Truncating 'processed_ingredients' (and cascading to 'ingredient_allergens')...")
    cur.execute("TRUNCATE TABLE processed_ingredients RESTART IDENTITY CASCADE;")
    conn.commit()
    print("[OK] Tables cleared.\n")

    create_sql = """
    CREATE TABLE IF NOT EXISTS processed_ingredients (
        id SERIAL PRIMARY KEY,
        recipe_id INTEGER NOT NULL,
        ingredient TEXT NOT NULL,
        FOREIGN KEY (recipe_id) REFERENCES clean_recipes(id)
    );
    """
    cur.execute(create_sql)
    conn.commit()
    print("[OK] Ensured 'processed_ingredients' exists.\n")

    cur.execute("SELECT id, ingredients FROM clean_recipes;")
    recipes = cur.fetchall()

    records = []
    for recipe_id, ing_text in recipes:
        if not ing_text:
            continue
        lines = [line.strip() for line in ing_text.splitlines() if line.strip()]
        for raw in lines:
            cleaned = normalize_ingredient(raw)
            if cleaned:
                records.append((recipe_id, cleaned))

    print(f"[INFO] {len(records)} cleaned ingredient records to insert.")

    if records:
        insert_sql = "INSERT INTO processed_ingredients (recipe_id, ingredient) VALUES (%s, %s);"
        cur.executemany(insert_sql, records)
        conn.commit()
        print(f"[OK] Inserted {len(records)} rows into 'processed_ingredients'.")
    else:
        print("[NOTE] No ingredients to insert.")

    cur.close()
    conn.close()
    print("[DONE] Database connection closed.")

if __name__ == "__main__":
    main()
