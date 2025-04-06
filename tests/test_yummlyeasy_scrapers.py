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
def yummly_scraper(db_connection):
    config_path = Path(__file__).parent.parent / "config" / "yummlyeasy.json"
    import json
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    config = config_data[0] if isinstance(config_data, list) else config_data
    scraper = BaseRecipeScraper(config)
    scraper.db_connection = db_connection
    scraper.db_cursor = db_connection.cursor()
    return scraper


def test_fetch_yummly_page(yummly_scraper):
    url = "https://yummlyeasy.com/category/all-recipes/"
    html = yummly_scraper.fetch_page(url)
    assert isinstance(html, str)
    assert "<html" in html.lower()


"""def test_parse_yummly_recipe(yummly_scraper):
    sample_html = """"""
    <html>
      <header class="entry-header"><h1 class="entry-title">Yummly Chocolate Cake</h1></header>
      <div class="entry-content">
        <ol>
          <li>1 cup flour</li>
        </ol>
        <ol>
          <li>Mix and bake</li>
        </ol>
      </div>
    </html>
    """"""
    parsed = yummly_scraper.parse_recipe(sample_html)
    assert "Yummly Chocolate Cake" in parsed["title"]
    assert "1 cup flour" in parsed["ingredients"]
    assert "Mix and bake" in parsed["instructions"]"""

def test_parse_yummly_recipe(yummly_scraper):
    sample_html = """
    <html>
      <header class="entry-header">
        <h1 class="entry-title">Yummly Chocolate Cake</h1>
      </header>
      <div class="entry-content">
        <ol>
          <li>1 cup flour</li>
        </ol>
        <ol>
          <li>This list is not used for instructions</li>
        </ol>
        <ol>
          <li>Mix and bake</li>
        </ol>
      </div>
    </html>
    """
    parsed = yummly_scraper.parse_recipe(sample_html)
    assert "Yummly Chocolate Cake" in parsed["title"]
    assert "1 cup flour" in parsed["ingredients"]
    assert "Mix and bake" in parsed["instructions"]


def test_gather_yummly_links(yummly_scraper):
    links = yummly_scraper.gather_recipe_links()
    assert isinstance(links, list)
    assert len(links) > 0
    assert all(link.startswith("http") for link in links)


def test_save_yummly_recipe_to_db(yummly_scraper):
    url = "http://example.com/yummly-test"
    raw_html = "<html><h1>Yummly Test</h1></html>"
    parsed_data = {
        "site_name": "Yummly Easy",
        "title": "Yummly Test Recipe",
        "ingredients": "Flour, Cocoa",
        "instructions": "Bake it!",
        "tags": "Dessert, Chocolate"
    }
    yummly_scraper.save_recipe(url, raw_html, parsed_data)
    cur = yummly_scraper.db_cursor
    cur.execute("SELECT id FROM raw_recipes WHERE url = %s", (url,))
    raw = cur.fetchone()
    assert raw
    raw_id = raw[0]
    cur.execute("SELECT recipe_title FROM clean_recipes WHERE raw_id = %s", (raw_id,))
    clean = cur.fetchone()
    assert clean
    yummly_scraper.db_connection.rollback()
