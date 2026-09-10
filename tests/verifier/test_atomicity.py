import sqlite3


def test_webhook_state_changes_are_atomic(client, db_path):
    created = client.post("/orders", json={"sku": "SKU-002", "quantity": 7})
    assert created.status_code == 201
    order_id = created.json()["id"]

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TRIGGER fail_atomic_audit
            BEFORE INSERT ON audit_logs
            WHEN NEW.event_id = 'evt-force-rollback'
            BEGIN
                SELECT RAISE(ABORT, 'forced audit failure');
            END;
            """
        )
        conn.commit()

    payload = {
        "event_id": "evt-force-rollback",
        "order_id": order_id,
        "event_type": "payment.completed",
        "sequence": 2,
    }
    response = client.post("/webhooks/payment", json=payload)
    assert response.status_code >= 500

    with sqlite3.connect(db_path) as conn:
        order = conn.execute(
            "SELECT status, last_event_sequence FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        inventory = conn.execute(
            "SELECT quantity FROM inventory WHERE sku = 'SKU-002'"
        ).fetchone()[0]
        event_count = conn.execute(
            "SELECT COUNT(*) FROM processed_events WHERE event_id = 'evt-force-rollback'"
        ).fetchone()[0]
        audit_count = conn.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE event_id = 'evt-force-rollback'"
        ).fetchone()[0]
        conn.execute("DROP TRIGGER fail_atomic_audit")
        conn.commit()

    assert order == ("PENDING", 0)
    assert inventory == 50
    assert event_count == 0
    assert audit_count == 0
