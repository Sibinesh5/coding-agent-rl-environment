def next_payment_status(current_status: str, event_type: str) -> str:
    if event_type == "payment.completed":
        return "PAID"
    if event_type == "payment.pending":
        return "PENDING"
    return current_status
