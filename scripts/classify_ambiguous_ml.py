#!/usr/bin/env python

import os
import sys
import joblib
import psycopg2
import numpy as np
import pandas as pd

from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

DB_URL = "postgresql://postgres:admin@localhost:5432/allergen_recipes"

# Compute project-relative paths
SCRIPT_DIR   = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Paths for training data and model artifacts
TRAIN_CSV  = os.path.join(PROJECT_ROOT, "data", "ambiguous_train.csv")
MODEL_DIR  = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "allergen_classifier.pkl")


def train_model():
    """
    Train a multi-label classifier on ambiguous ingredients.
    Expects TRAIN_CSV to have 'ingredient' and 'labels' columns.
    Saves the trained pipeline + label set to MODEL_PATH.
    """
    if not os.path.exists(TRAIN_CSV):
        print(f"[ERROR] Could not find training data: {TRAIN_CSV}")
        sys.exit(1)

    print(f"[TRAIN] Loading training data from '{TRAIN_CSV}'...")
    df = pd.read_csv(TRAIN_CSV)
    if "ingredient" not in df.columns or "labels" not in df.columns:
        print("[ERROR] CSV must have 'ingredient' and 'labels' columns.")
        sys.exit(1)

    # Convert 'labels' column from semicolon strings to lists
    df["labels"] = df["labels"].fillna("")
    all_label_sets = [
        [lbl.strip() for lbl in row.split(";") if lbl.strip()]
        for row in df["labels"]
    ]

    # Build the set of unique labels
    label_set = sorted({lbl for labs in all_label_sets for lbl in labs})

    # Create binary indicator matrix for multi-label classification
    Y = np.array([
        [1 if lbl in labs else 0 for lbl in label_set]
        for labs in all_label_sets
    ])

    X = df["ingredient"].astype(str).tolist()

    print(f"[TRAIN] {len(X)} samples, labels: {label_set}")

    # Build pipeline: TF-IDF vectorizer + One-vs-Rest logistic regression
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1,2), max_df=0.9, min_df=1)),
        ("clf", OneVsRestClassifier(LogisticRegression(max_iter=1000)))
    ])

    print("[TRAIN] Fitting the model...")
    pipeline.fit(X, Y)

    # Ensure the models directory exists
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Save the pipeline and label set
    joblib.dump((pipeline, label_set), MODEL_PATH)
    print(f"[TRAIN] Model saved to '{MODEL_PATH}'")


def classify_untagged_ingredients():
    """
    Load the trained model, find ingredients not yet tagged,
    predict allergens, and insert predictions into ingredient_allergens.
    """
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Model not found at '{MODEL_PATH}'. Run with --train first.")
        sys.exit(1)

    # Load model and labels
    pipeline, label_set = joblib.load(MODEL_PATH)
    print("[CLASSIFY] Loaded ML model.")

    # Connect to the database
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Select untagged ingredients 
    cur.execute("""
        SELECT pi.id, pi.recipe_id, pi.ingredient
        FROM processed_ingredients pi
        LEFT JOIN ingredient_allergens ia
          ON pi.id = ia.ingredient_id
        WHERE ia.ingredient_id IS NULL;
    """)
    rows = cur.fetchall()

    if not rows:
        print("[CLASSIFY] No untagged ingredients found.")
        cur.close()
        conn.close()
        return

    print(f"[CLASSIFY] {len(rows)} untagged ingredients found. Predicting...")

    texts = [r[2] for r in rows]
    ids_and_recipes = [(r[0], r[1]) for r in rows]

    preds = pipeline.predict(texts)

    to_insert = []
    for (ing_id, recipe_id), row_vec in zip(ids_and_recipes, preds):
        for idx, flag in enumerate(row_vec):
            if flag == 1:
                to_insert.append((ing_id, recipe_id, label_set[idx]))

    print(f"[CLASSIFY] {len(to_insert)} predictions to insert.")

    if to_insert:
        cur.executemany(
            "INSERT INTO ingredient_allergens (ingredient_id, recipe_id, allergen) VALUES (%s, %s, %s);",
            to_insert
        )
        conn.commit()
        print("[CLASSIFY] Inserted ML-predicted allergen tags.")

    cur.close()
    conn.close()
    print("[CLASSIFY] Done.")


def main():
    """
    Usage:
      python classify_ambiguous_ml.py --train   # to train and save model
      python classify_ambiguous_ml.py           # to classify untagged ingredients
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--train":
        train_model()
    else:
        classify_untagged_ingredients()


if __name__ == "__main__":
    main()
