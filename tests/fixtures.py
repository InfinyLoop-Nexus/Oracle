import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from data.database import engine, init_db, TEST_DB_PATH
from main import app
from data.models.user import User
from services.auth import HashHelper, get_auth, UserAuthData
import os
from services.environment_manager import get_environment


@pytest.fixture(scope="function")
def test_client():
    init_db(drop_existing=True)
    with TestClient(app) as client:
        yield client


def create_test_client_with_user(is_admin=False):
    init_db(drop_existing=True)
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=f"{HashHelper.hash('password')}",
    )
    user.admin = is_admin

    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
    environment = get_environment()
    auth = get_auth(environment)
    if user.id is None:
        raise ValueError("User ID cannot be None")
    token = auth.create_token(
        UserAuthData(username=user.username, user_id=user.id), trusted_client=True
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_client_as_admin():
    headers = create_test_client_with_user(is_admin=True)
    with TestClient(app) as client:
        client.headers = headers
        yield client


@pytest.fixture(scope="function")
def test_client_as_user():
    headers = create_test_client_with_user(is_admin=False)
    with TestClient(app) as client:
        client.headers = headers
        yield client


@pytest.fixture(scope="function")
def test_db_session():
    with Session(engine) as session:
        yield session
    engine.dispose()
    os.remove(TEST_DB_PATH)
