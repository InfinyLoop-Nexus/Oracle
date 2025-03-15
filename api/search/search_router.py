from fastapi import APIRouter, Depends, HTTPException, Body
from datetime import datetime
from services.auth import get_admin, get_user
from typing import List
from data.models.search import Search
from data.database import get_db
from sqlalchemy.orm import Session

search_router = APIRouter(prefix="/search")


@search_router.get("/", response_model=List[Search])
async def get_all_searches(admin=Depends(get_admin), db: Session = Depends(get_db)):
    return db.query(Search).all()


@search_router.get("/mine", response_model=List[Search])
async def get_search(user=Depends(get_user), db: Session = Depends(get_db)):
    return db.query(Search).filter(Search.user_id == user.id).all()


@search_router.post("/add")
async def upsert_search(
    search: Search, user=Depends(get_user), db: Session = Depends(get_db)
):
    if search.id is not None:
        existing_search = db.get(Search, search.id).first()
        if existing_search and existing_search.user_id != user.id and not user.admin:
            raise HTTPException(status_code=403, detail="You cannot update this search")
    search.user_id = user.id
    db.add(search)
    db.commit()
    db.refresh(search)
    return search


@search_router.post("/update")
async def update(
    body: str = Body(...), user=Depends(get_user), db: Session = Depends(get_db)
):
    search = Search.parse(body)
    if search.id is not None:
        existing_search = db.get(Search, search.id)
        if existing_search and existing_search.user_id != user.id and not user.admin:
            raise HTTPException(status_code=403, detail="You cannot update this search")
        elif existing_search is None:
            raise HTTPException(status_code=404, detail="Search not found")
    else:
        raise HTTPException(status_code=400, detail="Search id is required")

    existing_search.job_title = search.job_title
    existing_search.date_posted = search.date_posted
    existing_search.location = search.location
    existing_search.working_model = search.working_model
    existing_search.scraping_amount = search.scraping_amount
    existing_search.platform = search.platform
    existing_search.updated_at = datetime.now()

    db.commit()
    db.refresh(search)
    return search
