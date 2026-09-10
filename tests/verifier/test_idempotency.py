import sqlite3


def create_order(client, quantity=4):
    response = client.post("/orders", json={"sku": "SKU-001", "quantity": quantity})
    assert response.status_code == 201
    return response.json()["id"]


def state(db_path, order_id):
    with sqlite3.connect(db_path) as conn:
        order = conn.execute(
            "SELECT status, last_event_sequence FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        inventory = conn.execute(
            "SELECT quantity FROM inventory WHERE sku = 'SKU-001'"
        ).fetchone()[0]
        events = conn.execute(
            "SELECT COUNT(*) FROM processed_events WHERE order_id = ?", (order_id,)
        ).fetchone()[0]
        audits = conn.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE order_id = ?", (order_id,)
        ).fetchone()[0]
    return order, inventory, events, audits


def test_duplicate_completed_event_is_idempotent(client, db_path):
    order_id = create_order(client, quantity=4)
    payload = {
        "event_id": "evt-duplicate-001",
        "order_id": order_id,
        "event_type": "payment.completed",
        "sequence": 2,
    }

    for _ in range(3):
        response = client.post("/webhooks/payment", json=payload)
        assert response.status_code == 200
        assert response.json() == {"status": "processed"}

    order, inventory, events, audits = state(db_path, order_id)
    assert order == ("PAID", 2)
    assert inventory == 46
    assert events == 1
    assert audits == 1


def test_semantically_repeated_completion_does_not_double_apply(client, db_path):
    order_id = create_order(client, quantity=5)
    first = {
        "event_id": "evt-complete-a",
        "order_id": order_id,
        "event_type": "payment.completed",
        "sequence": 2,
    }
    second = {
        "event_id": "evt-complete-b",
        "order_id": order_id,
        "event_type": "payment.completed",
        "sequence": 3,
    }

    assert client.post("/webhooks/payment", json=first).status_code == 200
    assert client.post("/webhooks/payment", json=second).status_code == 200

    order, inventory, events, audits = state(db_path, order_id)
    assert order == ("PAID", 3)
    assert inventory == 45
    assert events == 2
    assert audits == 2
