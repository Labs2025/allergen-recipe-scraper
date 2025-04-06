import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import psycopg2
from pathlib import Path
from scrapers.base_scraper import BaseRecipeScraper


@pytest.fixture(scope="session")
def db_connection():
    conn = psycopg2.connect(
        dbname="allergen_recipes",
        user="postgres",
        password="admin",
        host="localhost",
        port=5432
    )
    yield conn
    conn.close()


@pytest.fixture
def afk_scraper(db_connection):
    config_path = Path(__file__).parent.parent / "config" / "theallergenfreekitchen.json"
    import json
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    config = config_data[0] if isinstance(config_data, list) else config_data
    scraper = BaseRecipeScraper(config)
    scraper.db_connection = db_connection
    scraper.db_cursor = db_connection.cursor()
    return scraper


def test_fetch_afk_page(afk_scraper):
    url = "https://www.theallergenfreekitchen.com/category/recipes/"
    html = afk_scraper.fetch_page(url)
    assert isinstance(html, str)
    assert "<html" in html.lower()


def test_parse_afk_recipe(afk_scraper):
    sample_html = """
    <html>
      <h1 class="entry-title">AFK Tofu Stir Fry</h1>
      <div class="wprm-recipe-ingredient-group">
        <ul class="wprm-recipe-ingredients">
          <li class="wprm-recipe-ingredient">Tofu</li>
          <li class="wprm-recipe-ingredient">Soy Sauce</li>
        </ul>
      </div>
      <div class="wprm-recipe-instruction-text">Cook tofu and mix with sauce</div>
    </html>
    """
    parsed = afk_scraper.parse_recipe(sample_html)
    assert "AFK Tofu Stir Fry" in parsed["title"]
    assert "Tofu" in parsed["ingredients"]
    assert "mix with sauce" in parsed["instructions"]


def test_gather_afk_links(afk_scraper):
    links = afk_scraper.gather_recipe_links()
    assert isinstance(links, list)
    assert len(links) > 0
    assert all(link.startswith("http") for link in links)


def test_save_afk_recipe_to_db(afk_scraper):
    url = "http://example.com/afk-test"
    raw_html = "<html><h1>AFK Test</h1></html>"
    parsed_data = {
        "site_name": "The Allergen Free Kitchen",
        "title": "AFK Test Recipe",
        "ingredients": "Tofu, Garlic",
        "instructions": "Stir fry tofu",
        "tags": "Test, Vegan"
    }
    afk_scraper.save_recipe(url, raw_html, parsed_data)
    cur = afk_scraper.db_cursor
    cur.execute("SELECT id FROM raw_recipes WHERE url = %s", (url,))
    raw = cur.fetchone()
    assert raw
    raw_id = raw[0]
    cur.execute("SELECT recipe_title FROM clean_recipes WHERE raw_id = %s", (raw_id,))
    clean = cur.fetchone()
    assert clean
    afk_scraper.db_connection.rollback()
