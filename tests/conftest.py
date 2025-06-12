# tests/conftest.py
import os
import sys
from pathlib import Path

import pytest

# ------------------------------------------------------------------
# 1) make sure the project root is importable
# ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]      # …/allergen_recipe_scraper
sys.path.insert(0, str(ROOT))

# ------------------------------------------------------------------
# 2) always use an in-memory SQLite DB for unit tests
#    (keeps tests independent from Postgres credentials)
# ------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app, db as _db

# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    """Create a fresh Flask app for the whole test session."""
    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,           # CSRF not needed for GET tests
    )

    with flask_app.app_context():
        _db.create_all()

    yield flask_app


@pytest.fixture(scope="session")
def client(app):
    """Reusable test client."""
    return app.test_client()
