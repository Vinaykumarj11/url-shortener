from datetime import UTC, datetime, timedelta

from app.config import Settings, get_settings
from app.main import app


def create(client, **payload):
    payload.setdefault("url", "https://example.com/some/long/path")
    return client.post("/api/v1/links", json=payload)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_redirect(client):
    res = create(client)
    assert res.status_code == 201
    body = res.json()
    assert len(body["code"]) == 7
    assert body["short_url"].endswith(body["code"])

    redirect = client.get(f"/{body['code']}", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com/some/long/path"


def test_clicks_are_counted_and_cached(client, redis_client):
    code = create(client).json()["code"]
    for _ in range(3):
        client.get(f"/{code}", follow_redirects=False)

    assert client.get(f"/api/v1/links/{code}").json()["clicks"] == 3
    assert redis_client.get(f"link:{code}") == "https://example.com/some/long/path"


def test_custom_code_conflict(client):
    assert create(client, custom_code="my-link").status_code == 201
    assert create(client, custom_code="my-link").status_code == 409


def test_invalid_url_rejected(client):
    assert create(client, url="not-a-url").status_code == 422


def test_unknown_code_404(client):
    assert client.get("/nope123", follow_redirects=False).status_code == 404


def test_expired_link_404(client):
    past = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    code = create(client, expires_at=past).json()["code"]
    assert client.get(f"/{code}", follow_redirects=False).status_code == 404


def test_delete_evicts_cache(client, redis_client):
    code = create(client).json()["code"]
    client.get(f"/{code}", follow_redirects=False)
    assert client.delete(f"/api/v1/links/{code}").status_code == 204
    assert redis_client.get(f"link:{code}") is None
    assert client.get(f"/{code}", follow_redirects=False).status_code == 404


def test_rate_limit(client):
    app.dependency_overrides[get_settings] = lambda: Settings(
        rate_limit_requests=2, database_url="sqlite:///./test.db"
    )
    assert create(client).status_code == 201
    assert create(client).status_code == 201
    res = create(client)
    assert res.status_code == 429
    assert "retry-after" in res.headers
