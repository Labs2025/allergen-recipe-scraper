import json
import os
from base_scraper import BaseRecipeScraper

if __name__ == "__main__":
    config_path = os.path.join("..", "config", "foodista.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    scraper = BaseRecipeScraper(config)
    scraper.run()
