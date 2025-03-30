import asyncio
from fastapi import APIRouter, WebSocket

websocket_router = APIRouter(prefix="/ws")


@websocket_router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.
    """
    await websocket.accept()
    await websocket.send_text("Hi!")

    while True:
        message = await websocket.receive_text()

        await websocket.send_text(f"Message recived was: {message}")

