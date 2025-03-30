from fastapi import APIRouter, WebSocket

websocket_router = APIRouter(prefix="/ws")

@websocket_router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.
    """
    # async def send_message(message: str):
    #     await websocket.send_text(message)
    #
    # async def receive_message():
    #     data = await websocket.receive_text()
    #     return data

    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        if (message == "Hello, WebSocket!"):
            await websocket.send_text("Hello, WebSocket!")