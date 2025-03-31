import pytest
import threading
import time
import uvicorn
import websockets
from main import app


@pytest.fixture(scope="module", autouse=True)
def run_server():
    config = uvicorn.Config(app, host="127.0.0.1", port=7999, log_level="info")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    time.sleep(1)
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

@pytest.mark.asyncio
async def test_websocket_ping():
    uri = "ws://localhost:7999/search/run-all"
    async with websockets.connect(uri) as websocket:
        response = await websocket.recv()
        assert response == "ping"
        await websocket.send("pong")
        await websocket.close(code=1000)

@pytest.mark.asyncio
async def test_websocket_ping():
    uri = "ws://localhost:7999/search/run-all"
    async with websockets.connect(uri) as websocket:
        response = await websocket.recv()
        assert response == "ping"
        try:
            await websocket.send("pang")
        except Exception as e:
            assert e.code == 1008
