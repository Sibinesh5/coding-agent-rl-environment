from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint
from .database import Base


class Inventory(Base):
    __tablename__ = "inventory"
    sku = Column(String, primary_key=True)
    quantity = Column(Integer, nullable=False)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    last_event_sequence = Column(Integer, nullable=False, default=0)


class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    __table_args__ = (UniqueConstraint("event_id", name="uq_processed_event_event_id"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, nullable=False)
    order_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    sequence = Column(Integer, nullable=False)
    applied = Column(Boolean, nullable=False, default=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False)
    event_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
