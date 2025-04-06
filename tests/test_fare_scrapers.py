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
def fare_scraper(db_connection):
    config_path = Path(__file__).parent.parent / "config" / "fare.json"
    import json
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    config = config_data[0] if isinstance(config_data, list) else config_data
    scraper = BaseRecipeScraper(config)
    scraper.db_connection = db_connection
    scraper.db_cursor = db_connection.cursor()
    return scraper


def test_fetch_fare_page(fare_scraper):
    url = "https://www.foodallergy.org/our-initiatives/awareness-campaigns/living-teal/feasting-fare"
    html = fare_scraper.fetch_page(url)
    assert isinstance(html, str)
    assert "<html" in html.lower()


def test_parse_fare_recipe(fare_scraper):
    sample_html = """
    <html>
      <div class="hero-secondary-text">
        <h1>Test FARE Recipe</h1>
        <p>Dairy-Free, Nut-Free</p>
      </div>
      <div class="center-column wysiwyg-content">
        <ul class="-split"><li>1 cup rice</li></ul>
        <ol><li>Cook rice</li></ol>
      </div>
    </html>
    """
    parsed = fare_scraper.parse_recipe(sample_html)
    assert "Test FARE Recipe" in parsed["title"]
    assert "1 cup rice" in parsed["ingredients"]
    assert "Cook rice" in parsed["instructions"]


def test_gather_fare_links(fare_scraper):
    links = fare_scraper.gather_recipe_links()
    assert isinstance(links, list)
    assert len(links) > 0
    assert all(link.startswith("http") for link in links)


def test_save_fare_recipe_to_db(fare_scraper):
    url = "http://example.com/fare-test"
    raw_html = "<html><h1>FARE Test</h1></html>"
    parsed_data = {
        "site_name": "FARE",
        "title": "FARE DB Recipe",
        "ingredients": "Rice, Water",
        "instructions": "Boil water, add rice",
        "tags": "Test, FARE"
    }
    fare_scraper.save_recipe(url, raw_html, parsed_data)
    cur = fare_scraper.db_cursor
    cur.execute("SELECT id FROM raw_recipes WHERE url = %s", (url,))
    raw = cur.fetchone()
    assert raw
    raw_id = raw[0]
    cur.execute("SELECT recipe_title FROM clean_recipes WHERE raw_id = %s", (raw_id,))
    clean = cur.fetchone()
    assert clean
    fare_scraper.db_connection.rollback()
