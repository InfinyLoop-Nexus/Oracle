import pytest
from fixtures import test_client_as_user
from asyncio import sleep

@pytest.mark.asyncio
async def test_websocket(test_client_as_user):
    """
    Test the WebSocket connection and message handling.
    """
    with test_client_as_user.websocket_connect("ws") as websocket:
        websocket.send_text("Hello, WebSocket!")
        data = websocket.receive_text()
        assert data == "Hello, WebSocket!"