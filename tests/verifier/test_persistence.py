import sqlite3


def test_idempotency_state_is_persisted(client, db_path):
    created = client.post("/orders", json={"sku": "SKU-001", "quantity": 2})
    order_id = created.json()["id"]
    payload = {
        "event_id": "evt-persisted-idempotency",
        "order_id": order_id,
        "event_type": "payment.completed",
        "sequence": 2,
    }
    assert client.post("/webhooks/payment", json=payload).status_code == 200

    with sqlite3.connect(db_path) as fresh_connection:
        stored = fresh_connection.execute(
            "SELECT order_id, event_type, sequence FROM processed_events WHERE event_id = ?",
            (payload["event_id"],),
        ).fetchone()
        inventory = fresh_connection.execute(
            "SELECT quantity FROM inventory WHERE sku = 'SKU-001'"
        ).fetchone()[0]

    assert stored == (order_id, "payment.completed", 2)
    assert inventory == 48
