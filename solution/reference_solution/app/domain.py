TERMINAL_PAYMENT_STATES = {"PAID"}


def next_payment_status(current_status: str, event_type: str) -> str:
    if current_status in TERMINAL_PAYMENT_STATES:
        return current_status
    if event_type == "payment.completed":
        return "PAID"
    if event_type == "payment.pending":
        return "PENDING"
    return current_status
