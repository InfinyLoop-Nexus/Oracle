import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from data.database import engine, init_db, TEST_DB_PATH
from main import app
import os


@pytest.fixture(scope="function")
def test_client():
    init_db(drop_existing=True)
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def test_db_session():
    with Session(engine) as session:
        yield session
    engine.dispose()
    os.remove(TEST_DB_PATH)
