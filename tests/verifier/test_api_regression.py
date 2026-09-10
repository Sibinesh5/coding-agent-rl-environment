def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_order_creation_and_read_contract(client):
    created = client.post("/orders", json={"sku": "SKU-001", "quantity": 3})
    assert created.status_code == 201
    body = created.json()
    assert body["sku"] == "SKU-001"
    assert body["quantity"] == 3
    assert body["status"] == "PENDING"
    assert body["last_event_sequence"] == 0

    fetched = client.get(f"/orders/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_unknown_order_and_sku_are_rejected(client):
    assert client.get("/orders/999999").status_code == 404
    assert client.post("/orders", json={"sku": "DOES-NOT-EXIST", "quantity": 1}).status_code == 404
