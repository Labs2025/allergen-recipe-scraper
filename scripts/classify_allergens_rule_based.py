#!/usr/bin/env python

import os
import json
import psycopg2


DB_URL = "postgresql://postgres:admin@localhost:5432/allergen_recipes"


def main():
    """
    1. Connect to the DB.
    2. Load allergen_dict.json.
    3. Ensure ingredient_allergens table exists.
    4. Fetch all processed ingredients.
    5. Perform rule-based allergen detection on each ingredient.
    6. Insert found allergens into ingredient_allergens.
    """

    print(f"Connecting to DB: {DB_URL}")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # 1. Load the allergen dictionary from JSON
    allergen_dict_path = "../config/allergen_dict.json" 
    if not os.path.exists(allergen_dict_path):
        print(f"[ERROR] Cannot find '{allergen_dict_path}'. Please create or place the file properly.")
        return

    with open(allergen_dict_path, "r", encoding="utf-8") as f:
        allergen_dict = json.load(f)

    print("[OK] Loaded allergen_dict.json.")

    # 2. Create ingredient_allergens table (if not exists)
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS ingredient_allergens (
            id SERIAL PRIMARY KEY,
            ingredient_id INTEGER NOT NULL,
            recipe_id INTEGER NOT NULL,
            allergen TEXT NOT NULL,
            FOREIGN KEY (ingredient_id) REFERENCES processed_ingredients(id),
            FOREIGN KEY (recipe_id) REFERENCES clean_recipes(id)
        );
    """
    cur.execute(create_table_sql)
    conn.commit()
    print("[OK] Ensured table 'ingredient_allergens' exists.\n")

    # 3. Fetch all processed ingredients from processed_ingredients
    fetch_sql = "SELECT id, recipe_id, ingredient FROM processed_ingredients;"
    cur.execute(fetch_sql)
    rows = cur.fetchall()
    print(f"Fetched {len(rows)} rows from processed_ingredients.")

    # We'll store the allergen tags we find in a list of tuples: (ingredient_id, recipe_id, allergen)
    allergen_records = []

    # 4. For each ingredient, we check if it contains any of the allergen keywords
    for ingredient_id, recipe_id, ingredient_text in rows:
        # We'll collect all allergens found for this single ingredient
        found_allergens = []
        
        # For each allergen, we have a list of keywords
        for allergen_name, keywords in allergen_dict.items():
            # We check if any of these keywords appear in the ingredient text
            # We'll do a simple substring search with word boundaries
            
            for keyword in keywords:
                text_lower = ingredient_text.lower()
                kw_lower = keyword.lower()
                
                if f" {kw_lower} " in f" {text_lower} " or text_lower == kw_lower:
                    found_allergens.append(allergen_name)
                    break  

        # After iterating all allergen categories, we add them to the aggregator
        for allergen_name in set(found_allergens):  
            allergen_records.append((ingredient_id, recipe_id, allergen_name))

    print(f"Found {len(allergen_records)} total allergen tags to insert into ingredient_allergens.")

    # 5. Insert them into the DB
    if allergen_records:
        insert_sql = """
            INSERT INTO ingredient_allergens (ingredient_id, recipe_id, allergen)
            VALUES (%s, %s, %s);
        """
        cur.executemany(insert_sql, allergen_records)
        conn.commit()
        print(f"[OK] Inserted {len(allergen_records)} rows into 'ingredient_allergens'.")
    else:
        print("[NOTE] No allergen matches found.")

    # Cleanup
    cur.close()
    conn.close()
    print("[DONE] Classification complete. Database connection closed.")


if __name__ == "__main__":
    main()
