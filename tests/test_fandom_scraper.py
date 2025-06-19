
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import psycopg2

from scrapers.base_scraper import BaseRecipeScraper

@pytest.fixture(scope="session")
def db_connection():
    conn = psycopg2.connect(
        dbname="allergen_recipes",
        user="postgres",
        password="admin",
        host="localhost",
        port=5432,
    )
    yield conn
    conn.close()


@pytest.fixture
def fandom_scraper(db_connection):
    config_path = Path(__file__).parent.parent / "config" / "fandom.json"
    with config_path.open(encoding="utf-8") as fh:
        import json

        cfg = json.load(fh)
    scraper = BaseRecipeScraper(cfg)

    scraper.db_connection = db_connection
    scraper.db_cursor = db_connection.cursor()
    return scraper


def test_fetch_fandom_page(fandom_scraper):
    url = (
        "https://recipes.fandom.com/wiki/Category:Main_Dish_Recipes"
    )
    html = fandom_scraper.fetch_page(url)
    assert isinstance(html, str)
    assert "<html" in html.lower()


def test_parse_fandom_recipe(fandom_scraper):
    sample_html = """
    <html>
      <h1 class="page-header__title" id="firstHeading">
        <span class="mw-page-title-main">Mock Fandom Dish</span>
      </h1>
      <div class="mw-content-ltr mw-parser-output">
        <ul>
          <li>2 cups rice</li>
          <li>1 tsp salt</li>
        </ul>
        <ol>
          <li>Boil water</li>
          <li>Add rice</li>
        </ol>
      </div>
    </html>
    """
    parsed = fandom_scraper.parse_recipe(sample_html)
    assert parsed["title"] == "Mock Fandom Dish"
    assert "2 cups rice" in parsed["ingredients"]
    assert "Boil water" in parsed["instructions"]


def test_gather_fandom_links(fandom_scraper):
    links = fandom_scraper.gather_recipe_links()
    assert isinstance(links, list)
    assert links, "No links found – selector may be wrong?"
    assert all(link.startswith("http") for link in links)


def test_save_fandom_recipe_to_db(fandom_scraper):
    url = "http://example.com/fandom-test"
    raw_html = "<html><h1>Fandom Test</h1></html>"
    parsed_data = {
        "site_name": "Fandom Recipes",
        "title": "Fandom Test Recipe",
        "ingredients": "Water, Flour",
        "instructions": "Mix then bake",
        "tags": "TestTag",
    }

    fandom_scraper.save_recipe(url, raw_html, parsed_data)

    cur = fandom_scraper.db_cursor
    cur.execute("SELECT id FROM raw_recipes WHERE url = %s", (url,))
    raw_row = cur.fetchone()
    assert raw_row, "raw_recipes insert failed"
    raw_id = raw_row[0]

    cur.execute(
        "SELECT recipe_title FROM clean_recipes WHERE raw_id = %s", (raw_id,)
    )
    clean_row = cur.fetchone()
    assert clean_row and clean_row[0] == "Fandom Test Recipe"

    fandom_scraper.db_connection.rollback()
