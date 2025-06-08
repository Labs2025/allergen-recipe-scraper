#!/usr/bin/env python
"""
classify_ambiguous_ml.py
------------------------

Small ML module that predicts allergens for *still-untagged* ingredients.
"""

from __future__ import annotations
import os
import sys
import joblib
import psycopg2
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier

# --------------------------------------------------------------------------- #
ROOT_DIR   = Path(__file__).resolve().parents[1]
DB_URL     = "postgresql://postgres:admin@localhost:5432/allergen_recipes"
TRAIN_CSV  = ROOT_DIR / "data" / "ambiguous_train.csv"
MODEL_DIR  = ROOT_DIR / "models"
MODEL_PATH = MODEL_DIR / "allergen_classifier.pkl"
# --------------------------------------------------------------------------- #

sys.path.append(str(ROOT_DIR))
from scripts.false_positive_guard import is_false_positive  # noqa: E402


# ╭──────────────────────────────────────────────────────────────────────────╮
# │ TRAINING                                                                │
# ╰──────────────────────────────────────────────────────────────────────────╯
def train_model() -> None:
    if not TRAIN_CSV.exists():
        sys.exit(f"[ERR] Training file missing: {TRAIN_CSV}")

    df = pd.read_csv(TRAIN_CSV)
    if not {"ingredient", "labels"}.issubset(df.columns):
        sys.exit("[ERR] CSV must have 'ingredient' and 'labels' columns")

    df["labels"] = df["labels"].fillna("")
    label_sets = [
        [lbl.strip() for lbl in row.split(";") if lbl.strip()]
        for row in df["labels"]
    ]
    vocab = sorted({lbl for row in label_sets for lbl in row})
    Y = np.array([[1 if l in row else 0 for l in vocab] for row in label_sets])
    X = df["ingredient"].astype(str).tolist()

    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_df=0.9, min_df=1)),
            ("clf", OneVsRestClassifier(LogisticRegression(max_iter=1000))),
        ]
    )

    print(f"[TRAIN] {len(X)} samples  | labels: {vocab}")
    pipe.fit(X, Y)

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump((pipe, vocab), MODEL_PATH)
    print(f"[TRAIN] model saved → {MODEL_PATH}")


# ╭──────────────────────────────────────────────────────────────────────────╮
# │ CLASSIFICATION                                                          │
# ╰──────────────────────────────────────────────────────────────────────────╯
def classify_untagged(threshold: float = 0.30) -> None:
    if not MODEL_PATH.exists():
        sys.exit("[ERR] Model not found – run with --train first")

    pipe, vocab = joblib.load(MODEL_PATH)
    print("[CLASSIFY] model loaded.")

    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()

    cur.execute(
        """
        SELECT pi.id, pi.recipe_id, pi.ingredient
        FROM processed_ingredients pi
        LEFT JOIN ingredient_allergens ia
          ON pi.id = ia.ingredient_id
        WHERE ia.ingredient_id IS NULL;
        """
    )
    rows = cur.fetchall()
    if not rows:
        print("[CLASSIFY] nothing to tag")
        cur.close(); conn.close(); return

    texts  = [r[2] or "" for r in rows]
    pairs  = [(r[0], r[1]) for r in rows]
    probs  = pipe.predict_proba(texts)

    inserts: list[tuple[int, int, str]] = []
    for (ing_id, recipe_id), prob_vec, raw_txt in zip(pairs, probs, texts):
        for idx, p in enumerate(prob_vec):
            if p >= threshold:
                allergen = vocab[idx]
                if not is_false_positive(allergen, raw_txt):
                    inserts.append((ing_id, recipe_id, allergen))

    print(f"[CLASSIFY] {len(inserts)} new tags")

    if inserts:
        cur.executemany(
            """
            INSERT INTO ingredient_allergens (ingredient_id, recipe_id, allergen)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            inserts,
        )
        conn.commit()
        print("[CLASSIFY] DB updated")

    cur.close(); conn.close()
    print("[DONE]")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--train":
        train_model()
    else:
        classify_untagged()


if __name__ == "__main__":
    main()
