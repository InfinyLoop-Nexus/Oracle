from fastapi import APIRouter, Depends, HTTPException, WebSocket
from fastapi.websockets import WebSocketDisconnect
from enum import Enum
from services.auth import get_admin, get_user
from typing import List
from data.models.search import Search
from data.database import get_db
from sqlmodel import Session, select

search_router = APIRouter(prefix="/search")


@search_router.get("/all", response_model=List[Search])
async def get_all_searches(admin=Depends(get_admin), db: Session = Depends(get_db)):
    return db.exec(select(Search)).all()


@search_router.get("/mine", response_model=List[Search])
async def get_searches(user=Depends(get_user), db: Session = Depends(get_db)):
    return db.exec(select(Search).where(Search.user_id == user.id)).all()


@search_router.post("/create")
async def create_search(
    search: Search, user=Depends(get_user), db: Session = Depends(get_db)
):
    if search.id:
        raise HTTPException(
            status_code=400, detail="Search id is not allowed for new search"
        )

    if user.id != search.user_id and not user.admin:
        raise HTTPException(
            status_code=403, detail="You cannot create a search for another user"
        )

    search.user_id = search.user_id if (user.admin and search.user_id) else user.id

    db.add(search)
    db.commit()
    return {"message": "Search created successfully"}


@search_router.post("/update")
async def update(search: Search, user=Depends(get_user), db: Session = Depends(get_db)):
    if not search.id:
        raise HTTPException(status_code=400, detail="Search id is required")

    existing_search = db.get(Search, search.id)

    if not existing_search:
        raise HTTPException(status_code=404, detail="Search not found")

    if existing_search.user_id != user.id and not user.admin:
        raise HTTPException(status_code=403, detail="You cannot update this search")

    update_data = search.model_dump(exclude_unset=True)

    ignored_fields = ["id", "user_id", "created_at", "updated_at"]
    for key, value in update_data.items():
        if key not in ignored_fields:
            setattr(existing_search, key, value)

    db.commit()
    return {"message": "Search updated successfully"}


@search_router.delete("/delete/{search_id}")
async def delete_search(
    search_id: int, user=Depends(get_user), db: Session = Depends(get_db)
):
    existing_search = db.get(Search, search_id)

    if not existing_search:
        raise HTTPException(status_code=404, detail="Search not found")

    if existing_search.user_id != user.id and not user.admin:
        raise HTTPException(status_code=403, detail="You cannot delete this search")

    db.delete(existing_search)
    db.commit()

    return {"message": "Search deleted successfully"}


class RunAllStep(Enum):
     START = "start {[nb_searches] : int ( nb_of_jobs )}"
     RUN = "running {current_search} {current_job}"
     FINISH = "finish"
@search_router.websocket("/run-all")
async def run(websocket: WebSocket, user=Depends(get_user), db: Session = Depends(get_db)):
    await websocket.accept()
    await websocket.send_text("ping")
    pong = await websocket.receive_text()
    if pong != "pong":
        await websocket.close(code=1008)

    # searches = db.exec(select(Search).where(Search.user_id == user.id)).all()


    return {"message": "Search run successfully"}
#  connect ws /search/run-all

@search_router.websocket("/health")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket health-check endpoint that echoes messages.

    Accepts a WebSocket connection, sends a "Hi!" greeting, and echoes each received message
    prefixed with "Message recived was: ".
    """
    try:
        await websocket.accept()
        await websocket.send_text("Hi!")
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"Message recived was: {message}")
    except WebSocketDisconnect:
        print("Client disconnected")
        pass
