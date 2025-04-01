import pytest
import threading
import time
import uvicorn
import websockets

from api.user.user_router import NewUserPayload, LoginPayload
from main import app
import requests
from data.models.user import User
import datetime
from services.auth import get_user


@pytest.fixture(scope="module", autouse=True)
def run_server():
    config = uvicorn.Config(app, host="127.0.0.1", port=7999, log_level="info")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    is_on = False
    while not is_on:
        try:
            print("i am trying")
            response = requests.get("http://localhost:7999/health")
            print("i tried once")
            if response.status_code == 200:
                is_on = True
            else:
                time.sleep(0.1)
        except:
            print("i excepted")
            pass
    print("i exited")

    yield

    # Shutdown
    server.should_exit = True
    thread.join()


@pytest.mark.asyncio
async def test_websocket():
    uri = "ws://localhost:7999/search/health"
    async with websockets.connect(uri) as websocket:
        response = await websocket.recv()
        assert response == "Hi!"

        await websocket.send("test")
        response = await websocket.recv()
        assert response == "Message recived was: test"


@pytest.mark.asyncio(scope="function")
async def test_websocket_ping():
    payload = NewUserPayload(
        username="testuser", email="testuser@example.com", password="TestPa$$w0rd"
    )
    requests.post("http://localhost:7999/user/create", json=payload.model_dump())
    login_payload = LoginPayload(username_or_email="testuser", password="TestPa$$w0rd")

    result = requests.post(
        "http://localhost:7999/user/login", json=login_payload.model_dump()
    )

    uri = "ws://localhost:7999/search/run-all"
    async with websockets.connect(uri) as websocket:
        response = await websocket.recv()
        assert response == "ping"
        await websocket.send("pong")
        await websocket.wait_closed()
        assert websocket.close_code == 1000


@pytest.mark.asyncio
async def test_websocket_ping_does_not_work():
    uri = "ws://localhost:7999/search/run-all"
    async with websockets.connect(uri) as websocket:
        response = await websocket.recv()
        assert response == "ping"
        try:
            await websocket.send("pang")
        except Exception as e:
            assert e.code == 1008
