from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import ProcessedEvent


def find_processed_event(db: Session, event_id: str) -> ProcessedEvent | None:
    return db.scalar(select(ProcessedEvent).where(ProcessedEvent.event_id == event_id))


def record_processed_event(
    db: Session,
    *,
    event_id: str,
    order_id: int,
    event_type: str,
    sequence: int,
    applied: bool,
) -> None:
    db.add(
        ProcessedEvent(
            event_id=event_id,
            order_id=order_id,
            event_type=event_type,
            sequence=sequence,
            applied=applied,
        )
    )
