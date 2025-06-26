# 🧑‍🍳 Allergen-Safe Recipe Scraper & Finder
 A full-stack proof-of-concept that **scrapes**, **classifies** and **serves** recipes free from the *14 major food-allergen* groups (EU / US overlap) – ready for immediate meal-plan filtering.

---

## ✨ Why this project?
* **240 M+** people world-wide live with food allergies.  
* Existing recipe sites rarely offer _reliable_ allergen filters.  
* Manual label-checking is slow and error-prone.  

This repo showcases how **web scraping + rule-based & ML NLP + a small Flask UI** can automate safe recipe discovery while respecting legal & ethical boundaries.


---

## 🔑 Features
| Area | Highlights |
|------|------------|
| **Scraping** | 6 allergy-friendly blogs, resilient selectors, request-retry, optional Selenium fallback |
| **DB schema** | `raw_recipes`, `clean_recipes`, `processed_ingredients`, `ingredient_allergens` *(FK-linked)* |
| **Allergen detection** | *Rule-based* dictionary ➕ *ML* classifier for ambiguous terms (`LogReg + TF-IDF`) |
| **Web UI** | Bootstrap 5, responsive cards, **modal popup** details, *Load more* pagination, **Clear filters** & *press Enter to search* |
| **Security** | CORS whitelisting, `Flask-WTF` CSRF demo, strict input validation, HTML escaping, common headers (`CSP`, `XFO`, `HSTS`) |
| **CI / Tests** | `pytest + coverage`, 90 %+ for API layer, `bandit` static scan |
| **Ops** | 🔄 Render .com cron job runs `scripts/run_full_pipeline.sh` nightly; writes logs to `/logs` |

---

## 🖥️ Quick Start (local)

# 1) clone & create env
git clone https://github.com/Labs2025/allergen-recipe-scraper.git
cd allergen-recipe-scraper
py -3.13 -m venv venv
venv\Scripts\activate          # (source venv/bin/activate on mac/linux)
pip install -r requirements.txt

# 2) bootstrap database (PostgreSQL 17 must be running)
psql -U postgres -f db_setup.sql -d allergen_recipes

# 3) scrape + process 
bash scripts/run_full_pipeline.sh

# 4) launch dev server
set FLASK_APP=app:create_app
flask run -p 5000
open http://127.0.0.1:5000

🛰️ Deployment (Render)
Create a PostgreSQL instance – copy DATABASE_URL.

New → Web Service → “Deploy from GitHub”.

Build command: pip install -r requirements.txt
Start command: gunicorn -b 0.0.0.0:10000 'app:create_app()'

Env vars

Key	Value
DATABASE_URL	(from step 1, starts with postgres://)
SECRET_KEY	any random string

Add a Cron Job (Render > Jobs) bash scripts/run_full_pipeline.sh – schedule daily.

🧪 Running tests

pytest -q --cov=app
bandit -r app

🔒 Security & Compliance
All HTTP inputs validated & HTML-escaped

CSRF token required on any future mutating routes (/api/secure-post demo)

Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Strict-Transport-Security added globally

Scrapers obey robots.txt, rate-limit and identify via UA string

Code scanned by bandit in CI


🙋 Disclaimer
Recipes and allergen classifications are best-effort automated results.
Always double-check ingredient labels and consult a medical professional if someone have severe allergies.