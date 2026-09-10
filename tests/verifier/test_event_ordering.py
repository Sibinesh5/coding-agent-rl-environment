import random
import sqlite3


def new_order(client, sku="SKU-001", quantity=2):
    response = client.post("/orders", json={"sku": sku, "quantity": quantity})
    assert response.status_code == 201
    return response.json()["id"]


def read_state(db_path, order_id, sku="SKU-001"):
    with sqlite3.connect(db_path) as conn:
        order = conn.execute(
            "SELECT status, last_event_sequence FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        inventory = conn.execute(
            "SELECT quantity FROM inventory WHERE sku = ?", (sku,)
        ).fetchone()[0]
    return order, inventory


def test_late_pending_event_cannot_regress_paid_order(client, db_path):
    order_id = new_order(client, quantity=3)
    completed = {
        "event_id": "evt-ordering-completed",
        "order_id": order_id,
        "event_type": "payment.completed",
        "sequence": 2,
    }
    late_pending = {
        "event_id": "evt-ordering-pending",
        "order_id": order_id,
        "event_type": "payment.pending",
        "sequence": 1,
    }

    assert client.post("/webhooks/payment", json=completed).status_code == 200
    assert client.post("/webhooks/payment", json=late_pending).status_code == 200

    assert read_state(db_path, order_id) == (("PAID", 2), 47)


def test_interleaved_duplicates_and_out_of_order_delivery(client, db_path):
    rng = random.Random(1337)
    order_ids = [new_order(client, quantity=1) for _ in range(6)]
    envelopes = []

    for index, order_id in enumerate(order_ids):
        pending = {
            "event_id": f"generated-{index}-pending-{rng.randrange(10**8, 10**9)}",
            "order_id": order_id,
            "event_type": "payment.pending",
            "sequence": 1,
        }
        completed = {
            "event_id": f"generated-{index}-completed-{rng.randrange(10**8, 10**9)}",
            "order_id": order_id,
            "event_type": "payment.completed",
            "sequence": 2,
        }
        envelopes.extend([completed, pending, completed.copy(), pending.copy()])

    rng.shuffle(envelopes)
    for payload in envelopes:
        response = client.post("/webhooks/payment", json=payload)
        assert response.status_code == 200

    with sqlite3.connect(db_path) as conn:
        paid_count = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'PAID'").fetchone()[0]
        inventory = conn.execute(
            "SELECT quantity FROM inventory WHERE sku = 'SKU-001'"
        ).fetchone()[0]
        distinct_events = conn.execute(
            "SELECT COUNT(DISTINCT event_id) FROM processed_events"
        ).fetchone()[0]
        total_events = conn.execute("SELECT COUNT(*) FROM processed_events").fetchone()[0]

    assert paid_count == 6
    assert inventory == 44
    assert distinct_events == 12
    assert total_events == 12
