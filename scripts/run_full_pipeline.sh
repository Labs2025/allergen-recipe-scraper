#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."   

if [[ -f "venv/Scripts/activate" ]]; then
  # shellcheck disable=SC1091
  source "venv/Scripts/activate"
elif [[ -f "venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "venv/bin/activate"
else
  echo "⚠️  No virtual-env found — using system Python" >&2
fi

LOG_DIR="logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/pipeline_$(date +%F_%H-%M-%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "==== $(date)  Pipeline started ===="

python scrapers/allergicliving_scraper.py
python scrapers/fandom_scraper.py
python scrapers/fare_scraper.py
python scrapers/foodista_scraper.py
python scrapers/theallergenfreekitchen_scraper.py
python scrapers/theprettybee_scraper.py
python scrapers/yummlyeasy_scraper.py
python scripts/clean_ingredients.py
python scripts/classify_allergens_rule_based.py
python scripts/classify_ambiguous_ml.py

echo "==== $(date)  Pipeline finished ===="
