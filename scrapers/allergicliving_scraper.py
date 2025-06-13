import json
import os
from base_scraper import BaseRecipeScraper
from pathlib import Path

if __name__ == "__main__":
    SCRIPT_DIR = Path(__file__).resolve().parent
    CONFIG_DIR = SCRIPT_DIR.parent / "config"
    config_path = CONFIG_DIR / "allergicliving.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    scraper = BaseRecipeScraper(config)
    scraper.run()
