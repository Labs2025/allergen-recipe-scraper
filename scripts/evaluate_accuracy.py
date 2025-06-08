#!/usr/bin/env python
# coding: utf-8
"""
Calculate precision, recall and F1 for rule-based and ML allergen classifiers
against a hand-labelled evaluation set.
"""
import sys, csv, psycopg2, itertools
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support, classification_report

DB_URL = "dbname=allergen_recipes user=postgres password=admin host=localhost"
ALLERGENS = [
 "Gluten","Milk","Egg","Fish","Crustaceans","Molluscs",
 "Tree Nuts","Peanuts","Soy","Sesame","Celery","Mustard",
 "Lupin","Sulphites"
]

def fetch_predicted(recipe_ids):
    """Return dict {recipe_id: set(allergens)} from ingredient_allergens."""
    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()
    ids_tuple = tuple(recipe_ids)
    cur.execute("""
        SELECT recipe_id, allergen
        FROM ingredient_allergens
        WHERE recipe_id IN %s
    """, (ids_tuple,))
    pred = {}
    for rid, allergen in cur.fetchall():
        pred.setdefault(rid, set()).add(allergen)
    cur.close(); conn.close()
    return pred

def main(labels_csv):
    df = pd.read_csv(labels_csv)
    recipe_ids = df["id"].tolist()
    gold = {row["id"]: set(str(row["true_allergens"]).split(";"))
            for _, row in df.iterrows()}
    preds = fetch_predicted(recipe_ids)

    y_true, y_pred = [], []
    for rid in recipe_ids:
        gt = gold.get(rid, set())
        pr = preds.get(rid, set())
        y_true.append([int(a in gt)  for a in ALLERGENS])
        y_pred.append([int(a in pr)  for a in ALLERGENS])

    report = classification_report(
        y_true, y_pred, target_names=ALLERGENS, zero_division=0
    )
    print("\n=== Precision / Recall / F1 by allergen ===")
    print(report)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts\\evaluate_accuracy.py path\\to\\evaluation_labels.csv")
    main(sys.argv[1])
