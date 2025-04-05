

-- ==========================================================================
-- TABLE 1: raw_recipes
-- Stores the raw HTML content and minimal metadata.
-- ==========================================================================

CREATE TABLE IF NOT EXISTS raw_recipes (
    id          SERIAL PRIMARY KEY,
    site_name   TEXT NOT NULL,
    url         TEXT NOT NULL UNIQUE,
    scraped_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    raw_html    TEXT NOT NULL
);

-- ==========================================================================
-- TABLE 2: clean_recipes
-- Stores the cleaned/parsed recipe data (e.g. title, ingredients, instructions).
-- Links back to raw_recipes via raw_id.
-- ==========================================================================

CREATE TABLE IF NOT EXISTS clean_recipes (
    id           SERIAL PRIMARY KEY,
    raw_id       INT REFERENCES raw_recipes(id) ON DELETE CASCADE,
    site_name    TEXT NOT NULL,
    recipe_title TEXT NOT NULL,
    ingredients  TEXT NOT NULL,
    instructions TEXT NOT NULL,
    tags         TEXT,
    scraped_at   TIMESTAMP NOT NULL DEFAULT NOW()
);



