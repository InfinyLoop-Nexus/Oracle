from fastapi import APIRouter, Depends, HTTPException
from services.auth import get_admin, get_user
from typing import List
from data.models.search import Search
from data.database import get_db
from sqlalchemy.orm import Session

search_router = APIRouter(prefix="/search")


@search_router.get("/read_all", response_model=List[Search])
async def read_all_searches(admin=Depends(get_admin), db: Session = Depends(get_db)):
    return db.query(Search).all()


@search_router.get("/read", response_model=List[Search])
async def read_searches(user=Depends(get_user), db: Session = Depends(get_db)):
    return db.query(Search).filter(Search.user_id == user.id).all()


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
    db.refresh(search)
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

    for key, value in update_data.items():
        setattr(existing_search, key, value)

    db.commit()
    db.refresh(existing_search)
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
