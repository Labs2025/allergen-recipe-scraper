"""
Coverage for app/routes.py – focus on validation,
escaping, CSRF protection and misc edge cases.
"""

import pytest
from flask_wtf.csrf import generate_csrf

API = "/api"


# --------------------------------------------------------------------------- #
#  basic path checks
# --------------------------------------------------------------------------- #
def test_allergens_ok(client):
    res = client.get(f"{API}/allergens")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 14
    assert all(isinstance(a, str) for a in data)


def test_search_random_limit(client):
    res = client.get(f"{API}/recipes?limit=3")
    assert res.status_code == 200
    assert len(res.get_json()) <= 3


# --------------------------------------------------------------------------- #
#  validation - limit
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad", ["abc", "-5", "0"])
def test_bad_limit_rejected(client, bad):
    res = client.get(f"{API}/recipes?limit={bad}")
    assert res.status_code == 400


# --------------------------------------------------------------------------- #
#  validation - unknown allergen
# --------------------------------------------------------------------------- #
def test_unknown_allergen_rejected(client):
    res = client.get(f"{API}/recipes?exclude=UnicornDust")
    assert res.status_code == 400


# --------------------------------------------------------------------------- #
#  XSS defence – &lt; script &gt; should be escaped
# --------------------------------------------------------------------------- #
def test_xss_escaped(client):
    evil = "<script>alert(1)</script>"
    res = client.get(f"{API}/recipes?q={evil}&limit=1")
    assert res.status_code == 200
    payload = res.get_json()[0]["title"]
    assert "<script>" not in payload
    assert "&lt;script&gt;" in payload


# --------------------------------------------------------------------------- #
#  CSRF guarded end-point
# --------------------------------------------------------------------------- #
def test_csrf_missing_rejected(client):
    res = client.post(f"{API}/secure-post", json={})
    assert res.status_code == 400


def test_csrf_invalid_rejected(client):
    res = client.post(f"{API}/secure-post", json={"csrf_token": "bogus"})
    assert res.status_code == 403


def test_valid_csrf(client, app):
    """
    1.  Make *any* GET (establishes a session)
    2.  Generate a token within that request ctx
    3.  POST with that token -> 200 OK
    """
    with client:                           
        client.get(f"{API}/allergens")     
        token = generate_csrf()            
        res = client.post(                 
            f"{API}/secure-post",
            json={"csrf_token": token},
        )
        assert res.status_code == 200
        assert res.get_json() == {"ok": True}
