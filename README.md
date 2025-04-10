Allergen Recipe Scraper

1. Project Overview

This repository provides a Python-based scraping framework to collect and classify online recipes according to the 14 major allergen groups. It automates data extraction from various websites using Requests, Selenium, and Beautiful Soup, then stores both raw HTML and cleaned recipe data (title, ingredients, instructions) in a PostgreSQL database.
Developers can easily adapt the scrapers for new sites by adjusting JSON config files (e.g., CSS selectors, start URLs) rather than editing code. The classification logic can also be extended or refined to detect additional allergens or specialized dietary constraints. Ultimately, the framework’s purpose is to facilitate rapid filtering of recipes based on specified allergen exclusions and support an optional user-facing web interface (e.g., built with Flask) for real-time queries.

Key Features:
•	Modular Scrapers: Separate scripts and config files for each target site, promoting maintainability.
•	Robust Data Flow: Raw data and parsed results both stored in the database for easy reference and analysis.
•	Extensible Classification: Plug in advanced ML/NLP or custom dictionaries to map ingredients to allergen categories.
•	Ethical & Legal Compliance: Rate-limited scraping, respect for robots.txt, and disclaimers regarding data usage.
Please see the subsequent sections for instructions on setup, configuring scrapers, and running tests.

2. Directory Structure
A clear folder layout ensures maintainability and scalability:

allergen_recipe_scraper/
├── scrapers/
│   ├── base_scraper.py              # Base class with shared scraper logic
│   ├── allergicliving_scraper.py    # One scraper script per target site
│   ├── fare_scraper.py              
│   ├── foodista_scraper.py
│   ├── theallergenfreekitchen_scraper.py
│   ├── theprettybee_scraper.py
│   └── yummlyeasy_scraper.py
│   
├── config/
│   ├── allergicliving.json          # Site-specific selectors and URLs
│   ├── fare.json
│   ├── foodista.json
│   ├── theallergenfreekitchen.json
│   ├── theprettybee.json
│   └── yummlyeasy.json
│                           
├── logs/
│   ├── allergicliving.log           # Log file for Allergic Living scraper
│   ├── theprettybee.log
│   └── ...                          # (One log per site)
├── tests/
│   ├── test_allergicliving_scrapers.py
│   ├── test_fare_scrapers.py
│   └── ...                          # (Other test files)
├── .github/                         
├── db_setup.sql                     # SQL script to create DB schema/tables
├── requirements.txt                 # Python packages and their versions.
└── README.md                        # Project documentation

Key Folders

scrapers/: Contains individual scraper scripts and a shared base_scraper.py.
config/: Holds configuration JSON files specifying CSS selectors, pagination logic, or usage of Selenium.
logs/: Each scraper writes to its own log file, aiding in debugging and record-keeping.
tests/: Integration and unit tests (Pytest-based).

3. Installation

- Clone the Repository

git clone https://github.com/Labs2025/allergen-recipe-scraper.git
cd allergen-recipe-scraper

- Set Up a Python Virtual Environment (recommended)

# For Windows:
python -m venv venv
venv\Scripts\activate

# For macOS/Linux:
python3 -m venv venv
source venv/bin/activate

- Install Project Dependencies

pip install -r requirements.txt

4. Database Setup

This project uses PostgreSQL to store both raw HTML and cleaned recipe data. If PostgreSQL is not already installed, follow the official documentation for your operating system.

- Create the Database
In a PostgreSQL console (e.g., psql):

CREATE DATABASE allergen_recipes;

- Create Tables
Run the provided db_setup.sql script:

psql -d allergen_recipes -U postgres -f db_setup.sql

This creates two tables:

- raw_recipes: Stores the raw HTML and minimal metadata.
- clean_recipes: Stores the parsed recipe data (title, ingredients, instructions, etc.).

- Update the Connection Parameters
By default, the scraper expects:
dbname="allergen_recipes"
user="postgres"
password="admin"
host="localhost"
port=5432
If your local settings differ, modify base_scraper.py accordingly in the __init__ method.

5. Configuration Files
Each site has a corresponding JSON file in the config/ directory. Key fields typically include:
site_name: Used for identification in logs and the database.
base_url: The home or root URL to resolve relative links.
start_urls: One or more listing pages where recipes are enumerated.
recipe_link_selector: CSS selector to grab the anchor tag(s) linking to individual recipes.
pagination_selector: (Optional) CSS selector if the site has paginated results.
title_selector, ingredients_selector, instructions_selector, tags_selector: CSS selectors to extract recipe details from a recipe page.
use_selenium: Boolean specifying whether to use Selenium (required for JavaScript-heavy pages).

Modifying the selectors or start URLs simply involves changing the JSON file rather than editing the Python code—this ensures modularity and ease of maintenance.

6. How to Run the Scrapers
Each scraper file (e.g., allergicliving_scraper.py) is designed as a standalone entry point:

# Example for Allergic Living:
python scrapers/allergicliving_scraper.py

# Example for The Pretty Bee:
python scrapers/theprettybee_scraper.py

The sequence is as follows:

- Initialize the BaseRecipeScraper with the corresponding config file (parsed automatically).
- Gather recipe links (including paginated pages, if applicable).
- Fetch each recipe page via Requests or Selenium.
- Parse the recipe details (title, ingredients, instructions, etc.).
- Insert both raw HTML (into raw_recipes) and cleaned data (into clean_recipes).

You will see log entries in the logs/ directory, indicating success or errors.

7. Logging
Each scraper writes to a dedicated log file in logs/:

- allergicliving.log
- theprettybee.log
- etc.

Logs contain:

- Timestamps
- Log level (INFO, ERROR, etc.)
- Descriptions of attempted URLs and any encountered errors

Review these files to diagnose failed requests, broken selectors, or database connection issues.

8. Testing
We use Pytest to validate scraper functionality, database inserts, and core logic. 
You can run the entire test suite from the project root:

pytest tests/ -v

Typical Test Scenarios
- Fetching Pages: Confirms the scraper retrieves HTML from known URLs.
- Parsing: Validates that the correct data (title, ingredients, instructions) is extracted from sample HTML snippets.
- Link Gathering: Ensures the scraper finds expected recipe URLs on listing pages.
- Database Insert: Verifies that both raw_recipes and clean_recipes are populated correctly.


