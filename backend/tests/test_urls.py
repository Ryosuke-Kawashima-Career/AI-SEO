def test_register_valid_url_returns_201(client):
    response = client.post(
        "/api/urls", json={"url": "https://adventure.inc/"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] >= 1
    assert body["url"].startswith("https://adventure.inc")
    assert body["label"] is None


def test_register_duplicate_url_returns_409(client):
    payload = {"url": "https://adventure.inc/"}
    first = client.post("/api/urls", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/api/urls", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "This URL is already registered"


def test_register_invalid_url_returns_422(client):
    response = client.post("/api/urls", json={"url": "not-a-url"})
    assert response.status_code == 422


def test_delete_existing_url_returns_204(client):
    created = client.post(
        "/api/urls", json={"url": "https://adventure.inc/hotels"}
    )
    url_id = created.json()["id"]

    response = client.delete(f"/api/urls/{url_id}")
    assert response.status_code == 204


def test_delete_nonexistent_url_returns_404(client):
    response = client.delete("/api/urls/99999")
    assert response.status_code == 404
