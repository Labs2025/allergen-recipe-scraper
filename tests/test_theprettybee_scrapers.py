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
def prettybee_scraper(db_connection):
    # Load config from theprettybee.json
    config_path = Path(__file__).parent.parent / "config" / "theprettybee.json"
    assert config_path.exists(), f"Config file not found: {config_path}"
    import json
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    config = config_data if isinstance(config_data, dict) else config_data[0]
    scraper = BaseRecipeScraper(config)
    scraper.db_connection = db_connection
    scraper.db_cursor = db_connection.cursor()
    return scraper

def test_fetch_prettybee_page(prettybee_scraper):
    url = "https://theprettybee.com/category/main-dishes/"
    html = prettybee_scraper.fetch_page(url)
    assert isinstance(html, str)
    assert "<html" in html.lower()

def test_parse_prettybee_recipe(prettybee_scraper):
    sample_html = """
    <html>
      <body>
        <header class="entry-header">
          <h1 class="entry-title">Pretty Bee Test Dish</h1>
          <h2 class="entry-title">
            <a class="entry-title-link" href="/some-link">Link</a>
          </h2>
        </header>
        <ul>
          <li class="wprm-recipe-ingredient">Test Ingredient A</li>
          <li class="wprm-recipe-ingredient">Test Ingredient B</li>
        </ul>
        <div class="wprm-recipe-instruction-text">Cook and serve warm.</div>
        <span class="wprm-recipe-cuisine">Italian</span>
      </body>
    </html>
    """
    parsed = prettybee_scraper.parse_recipe(sample_html)
    assert "Pretty Bee Test Dish" in parsed["title"]
    assert "Test Ingredient A" in parsed["ingredients"]
    assert "Cook and serve warm." in parsed["instructions"]
    # Check tags if available.
    if parsed.get("tags"):
        assert "Italian" in parsed["tags"]

def test_gather_prettybee_links(prettybee_scraper):
    links = prettybee_scraper.gather_recipe_links()
    assert isinstance(links, list)
    assert len(links) > 0, "Should find at least one recipe link"
    for link in links:
        assert link.startswith("http"), f"Invalid link: {link}"

def test_save_prettybee_recipe_to_db(prettybee_scraper):
    url = "http://example.com/prettybee-test"
    raw_html = "<html><h1>Pretty Bee DB Test</h1></html>"
    parsed_data = {
        "site_name": "The Pretty Bee",
        "title": "Pretty Bee DB Test Recipe",
        "ingredients": "Ingredient X\nIngredient Y",
        "instructions": "Mix ingredients and cook.",
        "tags": "Test, Cuisine"
    }
    prettybee_scraper.save_recipe(url, raw_html, parsed_data)
    cur = prettybee_scraper.db_cursor
    cur.execute("SELECT id FROM raw_recipes WHERE url = %s", (url,))
    raw = cur.fetchone()
    assert raw is not None
    raw_id = raw[0]
    cur.execute("SELECT recipe_title FROM clean_recipes WHERE raw_id = %s", (raw_id,))
    clean = cur.fetchone()
    assert clean is not None
    prettybee_scraper.db_connection.rollback()
