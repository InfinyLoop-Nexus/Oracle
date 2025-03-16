import uuid
from fastapi import APIRouter, Depends, HTTPException
from services.auth import get_admin, get_user
from typing import List
from data.models.job import Job
from data.models.rating import Rating
from data.database import get_db
from sqlmodel import select, Session

job_router = APIRouter(prefix="/jobs")


@job_router.get("/all", response_model=List[Job])
async def get_all_jobs(admin=Depends(get_admin), db: Session = Depends(get_db)):
    return db.query(Job).all()


@job_router.get("/mine", response_model=List[Job])
async def get_jobs(user=Depends(get_user), db: Session = Depends(get_db)):
    return [rating.job for rating in user.ratings]

@job_router.post("/create")
async def create_job(job: Job, user=Depends(get_user), db: Session = Depends(get_db)):
    if job.id:
        raise HTTPException(
            status_code=400, detail="Job id is not allowed for new job"
        )

    job.iid, generated = (job.iid, False) if job.iid else (str(uuid.uuid4()), True)

    existing_job = None if generated else db.exec(select(Job).where(Job.iid == job.iid)).first()

    if existing_job and db.exec(select(Rating).where(Rating.job_id == existing_job.id, Rating.user_id == user.id)).first():
        raise HTTPException(
            status_code=400, detail="Job already exists and has a rating for user"
        )

    with db.begin() as transaction:
        if not existing_job:
            db.add(job)
            db.flush()  # job.id is now generated

        jobid = existing_job.id if existing_job else job.id
        rating = Rating(job_id=jobid, user_id=user.id)
        db.add(rating)

    message = "The Job already existed and is now linked to your account" if existing_job else "The Job has been created"

    return {"message": message}


@job_router.post("/update")
async def update_job(job: Job, user=Depends(get_user), db: Session = Depends(get_db)):
    if not job.id:
        raise HTTPException(status_code=400, detail="Job id is required")

    existing_job = db.get(Job, job.id)
    if not existing_job:
        raise HTTPException(status_code=404, detail="Job not found")

    if existing_job.user_id != user.id and not user.admin:
        raise HTTPException(
            status_code=403, detail="You cannot update this job"
        )

    update_data = job.model_dump(exclude_unset=True)
    ignored_fields = ["id", "user_id", "created_at", "updated_at"]
    for key, value in update_data.items():
        if key not in ignored_fields:
            setattr(existing_job, key, value)

    db.commit()
    return {"message": "Job updated successfully"}


@job_router.delete("/delete/{job_id}")
async def delete_job(job_id: int, user=Depends(get_user), db: Session = Depends(get_db)):
    existing_job = db.get(Job, job_id)

    if not existing_job:
        raise HTTPException(status_code=404, detail="Job not found")

    if existing_job.user_id != user.id and not user.admin:
        raise HTTPException(
            status_code=403, detail="You cannot delete this job"
        )

    db.delete(existing_job)
    db.commit()

    return {"message": "Job deleted successfully"}