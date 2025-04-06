# File: tests/test_scrapers.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import psycopg2
from pathlib import Path

from scrapers.base_scraper import BaseRecipeScraper

@pytest.fixture(scope="session")
def db_connection():
    """
    A Pytest fixture that returns a live DB connection for tests.
    Closes automatically after the session is done.
    """
    try:
        conn = psycopg2.connect(
            dbname="allergen_recipes",
            user="postgres",
            password="admin",
            host="localhost",
            port=5432
        )
        yield conn
    finally:
        conn.close()

@pytest.fixture
def test_scraper(db_connection):
    """
    A fixture that creates and returns a BaseRecipeScraper instance
    using the config from allergicliving.json.
    """
    config_path = Path(__file__).parent.parent / "config" / "allergicliving.json"
    assert config_path.exists(), f"Config file not found: {config_path}"

    import json
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    if isinstance(config_data, list):
        config = config_data[0]
    else:
        config = config_data

    scraper = BaseRecipeScraper(config)
    scraper.db_connection = db_connection
    scraper.db_cursor = db_connection.cursor()
    return scraper

def test_fetch_page(test_scraper):
    """
    Test that fetching a known page via requests 
    returns HTML without error.
    """
    url = "https://www.allergicliving.com/recipe-category/allergy-friendly-kitchen-crafts/"
    html = test_scraper.fetch_page(url)
    assert isinstance(html, str), "fetch_page should return HTML as a string"
    assert "<html" in html.lower(), "Returned string should contain HTML"

def test_parse_recipe(test_scraper):
    """
    Test that parse_recipe extracts expected fields from sample HTML.
    Here we feed it a small snippet.
    """
    sample_html = """
    <html>
      <head><title>Test Recipe</title></head>
      <body>
        <article class="recipe recipe--large">
          <h1>Mock Allergy-Friendly Pancakes</h1>
          <div class="recipe__ingredients">
            <ul>
              <li>1 cup flour</li>
              <li>2 tbsp sugar</li>
            </ul>
          </div>
          <div class="recipe__instructions">
            <ol>
              <li>Mix ingredients.</li>
              <li>Cook on griddle.</li>
            </ol>
          </div>
        </article>
      </body>
    </html>
    """
    parsed = test_scraper.parse_recipe(sample_html)
    assert "Mock Allergy-Friendly Pancakes" in parsed["title"]
    assert "1 cup flour" in parsed["ingredients"]
    assert "Cook on griddle." in parsed["instructions"]

def test_gather_recipe_links(test_scraper):
    """
    Test that gather_recipe_links returns a list of URLs.
    """
    links = test_scraper.gather_recipe_links()
    assert isinstance(links, list), "gather_recipe_links should return a list"
    # Expect at least one link (depending on live content).
    assert len(links) > 0, "Should find at least one recipe link"
    for link in links:
        assert link.startswith("http"), "Each link should be an absolute URL"

def test_save_recipe_to_db(test_scraper):
    """
    Test the ability to insert raw HTML and parsed data into the DB.
    Verifies that a row is created in raw_recipes and clean_recipes.
    """
    url = "http://example.com/test-recipe"
    raw_html = "<html><h1>Test Recipe Insert</h1></html>"
    parsed_data = {
        "site_name": "TestSite",
        "title": "Inserted Test Recipe",
        "ingredients": "Flour, Sugar, Water",
        "instructions": "Mix all, Bake at 350F",
        "tags": "TestTag1, TestTag2",
    }

    test_scraper.save_recipe(url, raw_html, parsed_data)

    cur = test_scraper.db_cursor
    cur.execute("SELECT id, url, raw_html FROM raw_recipes WHERE url = %s", (url,))
    raw_row = cur.fetchone()
    assert raw_row is not None, "Entry should be inserted into raw_recipes"
    raw_id = raw_row[0]
    assert raw_row[1] == url, "URL must match"
    assert "Test Recipe Insert" in raw_row[2], "raw_html should contain expected text"

    cur.execute("SELECT raw_id, recipe_title, ingredients FROM clean_recipes WHERE raw_id = %s", (raw_id,))
    clean_row = cur.fetchone()
    assert clean_row is not None, "Entry should be inserted into clean_recipes"

    test_scraper.db_connection.rollback()
