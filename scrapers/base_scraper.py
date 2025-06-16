import os
import time
import json
import logging
import requests
import psycopg2
from bs4 import BeautifulSoup

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path         

ROOT_DIR = Path(__file__).resolve().parent.parent

LOG_DIR  = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True) 

class BaseRecipeScraper:
    """
    A base class to handle the common workflow of scraping recipe sites:
      1. Fetch a page (with requests or Selenium).
      2. Parse the page (collect recipe links or recipe details).
      3. Insert raw HTML and cleaned data into the database.

    """

    def __init__(self, config):
        """
        :param config: A dict loaded from JSON containing:
            - site_name (str)
            - start_urls (list)
            - recipe_link_selector (str)        # For listing pages
            - pagination_selector (str)         # (Optional) For multi-page listings
            - title_selector (str)
            - ingredients_selector (str)
            - instructions_selector (str)
            - tags_selector (str)
            - use_selenium (bool)
            
        """

        self.config = config
        self.site_name = config.get("site_name", "UnknownSite")
        self.start_urls = config.get("start_urls", [])

        # Logging setup
        
        log_filename = LOG_DIR / f"{self.site_name.lower().replace(' ', '_')}.log"
        logging.basicConfig(
            filename=str(log_filename),    
            filemode="a",
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            level=logging.INFO,
        )
        self.logger = logging.getLogger(self.site_name)

        # Database connection (
        try:
            db_url = os.getenv("DATABASE_URL", "")
            if db_url.lower().startswith("postgres"):
                # Render 
                self.db_connection = psycopg2.connect(db_url, sslmode="require")
            else:
                # Local default 
                self.db_connection = psycopg2.connect(
                    dbname=os.getenv("PGDATABASE", "allergen_recipes"),
                    user=os.getenv("PGUSER",     "postgres"),
                    password=os.getenv("PGPASSWORD", "admin"),
                    host=os.getenv("PGHOST",     "localhost"),
                    port=os.getenv("PGPORT",     5432),
                )

            self.db_cursor = self.db_connection.cursor()
            self.logger.info("Database connection established successfully.")
        except Exception as e:
            self.logger.error("Failed to connect to the database: %s", e)
            raise  # Stop execution if DB connection fails

        # Selenium or Requests?
        self.use_selenium = config.get("use_selenium", False)

        if self.use_selenium:
            # Configure headless Chrome for dynamic rendering
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            self.driver = webdriver.Chrome(options=chrome_options)
        else:
            # Requests Session with retry strategy
            self.session = requests.Session()
            retries = Retry(
                total=3, 
                backoff_factor=2,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retries)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)

        self.logger.info("Initialized scraper for site: %s", self.site_name)

                    
    def fetch_page(self, url):
        self.logger.info("Fetching URL: %s", url)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        if self.use_selenium:
            for attempt in range(3):
                try:
                    self.driver.get(url)
                    title_sel = self.config.get("title_selector")
                    if title_sel:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, title_sel))
                        )
                    html = self.driver.page_source
                    return html
                except Exception as e:
                    self.logger.error("Selenium attempt %d failed for %s: %s", attempt+1, url, e)
                    if attempt < 2:
                        time.sleep(2)
                    else:
                        raise
        else:
            try:
                response = self.session.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.text
            except Exception as e:
                self.logger.error("Requests failed to load: %s | Error: %s", url, e)
                raise e


    def parse_recipe(self, html):
        """
        Parse out the relevant recipe details from the HTML using Beautiful Soup.
        Returns a dict with keys: 'title', 'ingredients', 'instructions', 'tags', etc.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title_sel = self.config.get("title_selector", "")
        title_elem = soup.select_one(title_sel)
        title_text = title_elem.get_text(strip=True) if title_elem else "Untitled"

        # Ingredients
        ingredients_sel = self.config.get("ingredients_selector", "")
        ingredients_elems = soup.select(ingredients_sel)
        ingredients_list = [i.get_text(strip=True) for i in ingredients_elems]

        # Instructions
        instructions_sel = self.config.get("instructions_selector", "")
        instructions_elems = soup.select(instructions_sel)
        instructions_list = [i.get_text(strip=True) for i in instructions_elems]

        # Tags
        tags_sel = self.config.get("tags_selector", "")
        if tags_sel:
            tags_elems = soup.select(tags_sel)
            tags_list = [t.get_text(strip=True) for t in tags_elems]
        else:
            tags_list = []

        # Build final dictionary
        data = {
            "site_name": self.site_name,
            "title": title_text,
            "ingredients": "\n".join(ingredients_list),
            "instructions": "\n".join(instructions_list),
            "tags": ", ".join(tags_list),
        }
        return data

    def save_recipe(self, url, raw_html, parsed_data):
        """
        Insert the raw HTML into raw_recipes,
        then insert the cleaned recipe data into clean_recipes.
        """
        try:
            # Insert into raw_recipes (check for duplicate URL)
            insert_raw = """
                INSERT INTO raw_recipes (site_name, url, raw_html)
                VALUES (%s, %s, %s)
                ON CONFLICT (url) DO NOTHING
                RETURNING id;
            """
            self.db_cursor.execute(insert_raw, (self.site_name, url, raw_html))
            raw_id = self.db_cursor.fetchone()

            if not raw_id:
                # Retrieve existing ID for linking in clean_recipes
                self.db_cursor.execute("SELECT id FROM raw_recipes WHERE url = %s;", (url,))
                existing = self.db_cursor.fetchone()
                raw_id = existing if existing else (None,)
            raw_id = raw_id[0]  # raw_id is a tuple

            # Insert into clean_recipes
            insert_clean = """
                INSERT INTO clean_recipes
                (raw_id, site_name, recipe_title, ingredients, instructions, tags, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (site_name, recipe_title)                       
                DO UPDATE
                   SET raw_id       = EXCLUDED.raw_id,
					   ingredients  = EXCLUDED.ingredients,
                       instructions = EXCLUDED.instructions,
                       tags         = EXCLUDED.tags,
                       scraped_at   = NOW();
            """
            self.db_cursor.execute(
                insert_clean,
                (
                    raw_id,
                    parsed_data["site_name"],
                    parsed_data["title"],
                    parsed_data["ingredients"],
                    parsed_data["instructions"],
                    parsed_data["tags"],
                )
            )

            self.db_connection.commit()
            self.logger.info("Saved recipe: '%s' (URL: %s)", parsed_data["title"], url)
        except Exception as e:
            self.db_connection.rollback()
            self.logger.error("Database error saving recipe from %s: %s", url, e) 

    def gather_recipe_links(self):
        """
        Collect recipe links by crawling the 'start_urls' and following pagination if configured.
        Returns a list of unique URLs.
        """
        all_links = []
        link_sel = self.config.get("recipe_link_selector", "")
        pag_sel = self.config.get("pagination_selector", "")
        visited_pages = set()
        
        base_url = self.config.get("base_url", self.start_urls[0])

        def fetch_and_extract(url):
            """Local helper function to fetch a page, gather recipe links, find 'next' link."""
            try:
                page_html = self.fetch_page(url)
            except Exception as err:
                self.logger.error("Failed to fetch page %s: %s", url, err)
                return None, None

            soup = BeautifulSoup(page_html, "html.parser")
            # Extract recipe detail links
            #recipe_links = [a.get("href") for a in soup.select(link_sel) if a.get("href")]
            
            recipe_links = []
            for a in soup.select(link_sel):
                href = a.get("href")
                if href:
                    absolute_href = urljoin(base_url, href)
                    recipe_links.append(absolute_href)
            
            # Extract next-page link if any
            next_elem = soup.select_one(pag_sel) if pag_sel else None
            next_url = next_elem.get("href") if next_elem else None
#
            if next_url:
                next_url = urljoin(base_url, next_url)

            return recipe_links, next_url

        # Loop over each start URL
        for start_url in self.start_urls:
            current_url = start_url
            while current_url and current_url not in visited_pages:
                visited_pages.add(current_url)
                recipe_links, next_url = fetch_and_extract(current_url)
                if recipe_links:
                    all_links.extend(recipe_links)
                current_url = next_url

        unique_links = list(set(all_links))
        self.logger.info("Found %d unique recipe links for site '%s'.",
                         len(unique_links), self.site_name)
        return unique_links

    def run(self):
        """
        Main entry point:
          1. Gather all recipe links (including pagination).
          2. For each link, fetch, parse, and save data to the DB.
          3. If Selenium is in use, close the browser at the end.
        """
        try:
            links = self.gather_recipe_links()
            for link in links:
                try:
                    html = self.fetch_page(link)
                    parsed = self.parse_recipe(html)
                    self.save_recipe(link, html, parsed)
                except Exception as e:
                    self.logger.error("Error on link %s: %s", link, e)
                    # Skip and continue to next link

        finally:
            # Cleanup
            if self.use_selenium:
                self.driver.quit()
            self.db_cursor.close()
            self.db_connection.close()
            self.logger.info("Scraper finished for site: %s", self.site_name)
