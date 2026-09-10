from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from .database import Base, SessionLocal, engine, get_db
from .models import Inventory
from .repositories.orders import create_order, get_order
from .schemas import OrderCreate, OrderOut, PaymentWebhook
from .services.webhook_service import process_payment_webhook


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for sku in ("SKU-001", "SKU-002"):
            if db.get(Inventory, sku) is None:
                db.add(Inventory(sku=sku, quantity=50))
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="Webhook Reliability Service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/orders", response_model=OrderOut, status_code=201)
def post_order(payload: OrderCreate, db: Session = Depends(get_db)):
    inventory = db.get(Inventory, payload.sku)
    if inventory is None:
        raise HTTPException(status_code=404, detail="sku not found")
    return create_order(db, payload.sku, payload.quantity)


@app.get("/orders/{order_id}", response_model=OrderOut)
def read_order(order_id: int, db: Session = Depends(get_db)):
    order = get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return order


@app.post("/webhooks/payment")
def payment_webhook(payload: PaymentWebhook, db: Session = Depends(get_db)):
    process_payment_webhook(db, payload)
    return {"status": "processed"}
