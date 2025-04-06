

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
    Returns a PostgreSQL DB connection for use in tests.
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
def foodista_scraper(db_connection):
    """
    Loads the Foodista config and returns a scraper instance.
    """
    config_path = Path(__file__).parent.parent / "config" / "foodista.json"
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


def test_fetch_foodista_page(foodista_scraper):
    """
    Tests that the Foodista category page loads and returns HTML content.
    """
    url = "https://www.foodista.com/community-recipes"
    html = foodista_scraper.fetch_page(url)
    assert isinstance(html, str), "Expected HTML string"
    assert "<html" in html.lower(), "Page should contain HTML"


def test_parse_foodista_recipe(foodista_scraper):
    """
    Tests parsing logic against a mock HTML resembling Foodista's structure.
    """
    sample_html = """
    <html>
      <head><title>Foodista Test</title></head>
      <body>
        <h1 class="title" id="page-title">Test Pasta Primavera</h1>
        <div class="field-items">
            <div itemprop="ingredients">1 cup pasta</div>
            <div itemprop="ingredients">1 tbsp olive oil</div>
        </div>
        <div class="step-body" itemprop="recipeInstructions">Boil pasta. Add olive oil.</div>
      </body>
    </html>
    """
    parsed = foodista_scraper.parse_recipe(sample_html)
    assert "Test Pasta Primavera" in parsed["title"]
    assert "1 cup pasta" in parsed["ingredients"]
    assert "Boil pasta" in parsed["instructions"]


def test_gather_foodista_links(foodista_scraper):
    """
    Verifies that Foodista scraper finds recipe links from listing page.
    """
    links = foodista_scraper.gather_recipe_links()
    assert isinstance(links, list), "Should return a list of links"
    assert len(links) > 0, "Should find at least one recipe link"
    for link in links:
        assert link.startswith("http"), f"Invalid link: {link}"


def test_save_foodista_recipe_to_db(foodista_scraper):
    """
    Tests saving a test recipe to raw_recipes and clean_recipes tables.
    """
    url = "http://example.com/foodista-test"
    raw_html = "<html><h1>Foodista DB Test</h1></html>"
    parsed_data = {
        "site_name": "Foodista",
        "title": "Foodista DB Test Recipe",
        "ingredients": "Ingredient1\nIngredient2",
        "instructions": "Step 1. Step 2.",
        "tags": "Test, Example"
    }

    foodista_scraper.save_recipe(url, raw_html, parsed_data)

    cur = foodista_scraper.db_cursor
    cur.execute("SELECT id FROM raw_recipes WHERE url = %s", (url,))
    raw = cur.fetchone()
    assert raw is not None, "raw_recipes insert failed"

    raw_id = raw[0]
    cur.execute("SELECT recipe_title FROM clean_recipes WHERE raw_id = %s", (raw_id,))
    clean = cur.fetchone()
    assert clean is not None, "clean_recipes insert failed"

    # Clean up test data
    foodista_scraper.db_connection.rollback()
