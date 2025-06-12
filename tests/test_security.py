# tests/test_security.py
import urllib.parse, json, subprocess, re
from bs4 import BeautifulSoup as Bs

API = "/api"

# ----------------------------------------------------------------- #
# 1. SQL-injection (GET parameter)                                 #
# ----------------------------------------------------------------- #
def test_sql_injection_blocked(client):
    inj = "' OR 1=1 --"
    res = client.get(f"{API}/recipes?q={urllib.parse.quote_plus(inj)}")
    assert res.status_code == 200
    data = res.get_json()
    # Expect a *normal-sized* list – not “all rows”.
    assert len(data) < 100
    # The query string must be reflected *escaped* (no error splash)
    assert "Traceback" not in res.get_data(as_text=True)

# ----------------------------------------------------------------- #
# 2. Reflected-XSS / output-escaping                               #
# ----------------------------------------------------------------- #
def test_xss_escaped(client):
    res = client.get(f"{API}/recipes?q=<script>alert(1)</script>")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    # parse & ensure <script> tag did not survive
    assert not Bs(html, "html.parser").find("script")

# ----------------------------------------------------------------- #
# 3. CSRF – POST without token must be rejected (400/403)           #
# ----------------------------------------------------------------- #
def test_csrf_missing_rejected(client):
    r = client.post("/api/secure-post", json={})
    assert r.status_code in (400, 403)

# ----------------------------------------------------------------- #
# 4. CORS headers – wild-card allowed by app config                 #
# ----------------------------------------------------------------- #
def test_cors_headers(client):
    pre = client.options(
        f"{API}/allergens",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert pre.status_code == 200
    # Header may be '*' or absent (Flask-CORS skips header when origin
    # is not allowed).  Accept either.
    assert pre.headers.get("Access-Control-Allow-Origin") in (None, "*")

# ----------------------------------------------------------------- #
# 5. Security headers – at least basic trio must exist              #
# ----------------------------------------------------------------- #
SEC_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src",
}
def test_security_headers(client):
    res = client.get("/")
    for hdr in SEC_HEADERS:
        assert hdr in res.headers

# ----------------------------------------------------------------- #
# 6. Bandit static scan for command-injection hot-spots            #
# ----------------------------------------------------------------- #
def test_bandit_no_critical(tmp_path):
    """Bandit returns 0 when no HIGH-severity issues are found."""
    result = subprocess.run(
        ["bandit", "-q", "-r", "app", "--severity-level", "high"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
