#!/usr/bin/env python
"""
classify_allergens_rule_based.py
--------------------------------
Improved rule-based classifier:

* multi-word keywords handled robustly
* punctuation / dash tolerant
* optional plural “s” automatically allowed
* false-positive guard integration
"""

from __future__ import annotations
import os
import sys
import json
import re
from pathlib import Path
import psycopg2

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))
from scripts.false_positive_guard import is_false_positive 

# --------------------------------------------------------------------------- #
DB_URL     = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:admin@localhost:5432/allergen_recipes",
             ).replace("postgres://", "postgresql://", 1)
DICT_PATH  = ROOT_DIR / "config" / "allergen_dict.json"
# --------------------------------------------------------------------------- #


def compile_dictionary(raw: dict[str, list[str]]) -> dict[str, list[re.Pattern]]:
    """
    Turn every keyword into a regex that tolerates *any* non-word chars
    (space, dash, comma, slash) between tokens.
    """
    bucket: dict[str, list[re.Pattern]] = {}
    for allergen, keywords in raw.items():
        pats: list[re.Pattern] = []
        for kw in keywords:
            parts = kw.lower().split()
            joined = r"\W*".join(map(re.escape, parts))
            if not joined.endswith("s"):
                joined = f"{joined}s?"       
            pats.append(re.compile(rf"\b{joined}\b", re.I))
        bucket[allergen] = pats
    return bucket


def main() -> None:
    print(f"[DB] Connecting to {DB_URL}")
    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()

    if not DICT_PATH.exists():
        sys.exit(f"[ERR] missing dictionary: {DICT_PATH}")
    with DICT_PATH.open(encoding="utf-8") as fh:
        dict_raw = json.load(fh)
    dict_rgx = compile_dictionary(dict_raw)
    print("[OK] Loaded allergen dictionary")

    # ensure target table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ingredient_allergens (
            id            SERIAL PRIMARY KEY,
            ingredient_id INTEGER NOT NULL,
            recipe_id     INTEGER NOT NULL,
            allergen      TEXT    NOT NULL,
            UNIQUE (ingredient_id, allergen),
            FOREIGN KEY (ingredient_id) REFERENCES processed_ingredients(id),
            FOREIGN KEY (recipe_id)     REFERENCES clean_recipes(id)
        );
        """
    )
    conn.commit()

    # fetch every processed ingredient
    cur.execute("SELECT id, recipe_id, ingredient FROM processed_ingredients;")
    rows = cur.fetchall()
    print(f"[OK] {len(rows)} ingredients to scan")

    results: list[tuple[int, int, str]] = []

    for ing_id, recipe_id, txt in rows:
        text = txt or ""
        lower = text.lower()

        for allergen, regex_list in dict_rgx.items():
            if any(rgx.search(lower) for rgx in regex_list):
                if not is_false_positive(allergen, lower):
                    results.append((ing_id, recipe_id, allergen))

    print(f"[OK] {len(results)} tags identified")

    if results:
        cur.executemany(
            """
            INSERT INTO ingredient_allergens (ingredient_id, recipe_id, allergen)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            results,
        )
        conn.commit()
        print("[DB] Tags inserted")

    cur.close()
    conn.close()
    print("[DONE] Rule-based pass finished")


if __name__ == "__main__":
    main()
