import pytest
import threading
import time
import uvicorn
import websockets
from main import app
import requests
from data.models.user import User
import datetime
from services.auth import get_user


@pytest.fixture(scope="module", autouse=True)
def run_server():
    app.dependency_overrides[get_user] = lambda: User(
        id=1,
        create_at=datetime.datetime.now(),
        update_at=datetime.datetime.now(),
        username="something",
        email="something",
        password_hash="something",
        tokens_spent_lifetime=0,
        tokens_spent_current_month=0,
        tokens_spent_counter=0,
        home_address="",
        self_assessment="",
        job_prototype="",
        job_preferences="",
        job_dislikes="",
        desired_compensation="",
        cover_letter="",
        resume="",
        encoded_openai_api_key="",
        duplicate_behavior="skip_duplicates",
        admin=False,
    )
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
            pass

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
    uri = "ws://localhost:7999/search/run-all"
    async with websockets.connect(uri) as websocket:
        response = await websocket.recv()
        assert response == "ping"
        await websocket.send("pong")
        await websocket.wait_closed()

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
