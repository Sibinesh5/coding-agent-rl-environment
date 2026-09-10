import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TARGET_REPO = Path(os.environ.get("TARGET_REPO", "/workspace")).resolve()
DB_DIR = Path(tempfile.mkdtemp(prefix="coding_rl_verifier_"))
DB_PATH = DB_DIR / "verifier.db"
os.environ["APP_DATABASE_URL"] = f"sqlite:///{DB_PATH}"
sys.path.insert(0, str(TARGET_REPO))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Inventory  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add_all([
            Inventory(sku="SKU-001", quantity=50),
            Inventory(sku="SKU-002", quantity=50),
        ])
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def db_path() -> Path:
    return DB_PATH


def scalar(db_path: Path, query: str, params=()):
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(query, params).fetchone()
    return None if row is None else row[0]
