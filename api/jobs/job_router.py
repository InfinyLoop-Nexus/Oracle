import uuid
from fastapi import Query, APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.auth import get_admin, get_user
from typing import List
from data.models.job import Job
from data.models.rating import Rating
from data.database import get_db
from sqlmodel import select, Session

job_router = APIRouter(prefix="/jobs")


@job_router.get("/all", response_model=List[Job])
async def get_all_jobs(admin=Depends(get_admin), db: Session = Depends(get_db)):
    """
    Retrieve all jobs.

    This endpoint is restricted to admin users only.

    - **Authentication:** Requires admin privileges.
    - **Returns:** A list of all Job records.

    **Errors:**
    - 403 Forbidden if the user is not an admin.
    """
    return db.exec(select(Job)).all()


@job_router.get("/mine", response_model=List[Job])
async def get_jobs(user=Depends(get_user)):
    """
    Retrieve jobs linked to your account.

    This endpoint returns only the jobs that you have rated or are linked to your account.

    - **Authentication:** User must be logged in.
    - **Returns:** A list of Job records associated with your ratings.
    """
    return [rating.job for rating in user.ratings]


@job_router.get("/active", response_model=List[Job])
async def get_active(user=Depends(get_user)):
    """
    Retrieve your active jobs.

    Only jobs that are not archived (active) will be returned.

    - **Authentication:** User must be logged in.
    - **Returns:** A list of active Job records (i.e. where the associated rating is not archived).
    """
    return [rating.job for rating in user.ratings if not rating.archived]


@job_router.get("/archived", response_model=List[Job])
async def get_archived(user=Depends(get_user)):
    """
    Retrieve your archived jobs.

    This endpoint returns only jobs that have been archived.

    - **Authentication:** User must be logged in.
    - **Returns:** A list of archived Job records.
    """
    return [rating.job for rating in user.ratings if rating.archived]


@job_router.post("/create")
async def create_job(job: Job, user=Depends(get_user), db: Session = Depends(get_db)):
    """
    Create a new job and link it to your account.

    **Request Body:** A Job object without an `id`.

    - If a job with the same `iid` already exists and you do not have a rating for it,
      a new rating will be created linking you to the existing job.
    - If the job exists and you already have a rating, a 400 error is returned.

    **Authentication:** User must be logged in.

    **Returns:** A JSON message indicating whether the job was created or linked.

    **Errors:**
    - 400 if the payload contains an `id` or if a rating already exists for the job.
    - 500 if the job ID could not be determined.
    """
    if job.id:
        raise HTTPException(status_code=400, detail="Job id is not allowed for new job")

    job.iid, generated = (job.iid, False) if job.iid else (str(uuid.uuid4()), True)

    existing_job = (
        None if generated else db.exec(select(Job).where(Job.iid == job.iid)).first()
    )

    if (
        existing_job
        and db.exec(
            select(Rating).where(
                Rating.job_id == existing_job.id, Rating.user_id == user.id
            )
        ).first()
    ):
        raise HTTPException(
            status_code=400, detail="Job already exists and has a rating for user"
        )

    if not existing_job:
        db.add(job)
        db.flush()

    jobid = existing_job.id if existing_job else job.id
    if jobid is None:
        raise HTTPException(status_code=500, detail="Job ID could not be determined")
    rating = Rating(job_id=jobid, user_id=user.id)
    db.add(rating)
    db.commit()

    message = (
        "The Job already existed and is now linked to your account"
        if existing_job
        else "The Job has been created"
    )

    return {"message": message}


@job_router.post("/archive/{job_id}")
async def archive_job(
    job_id: int, user=Depends(get_user), db: Session = Depends(get_db)
):
    """
    Archive a job linked to your account.

    **Path Parameter:**
    - `job_id`: The unique identifier of the job to archive.

    **Authentication:** User must be logged in.

    **Returns:** A JSON message confirming the job has been archived.

    **Errors:**
    - 404 if the job (rating) is not found.
    - 400 if the job is already archived.
    """
    user_rating = db.exec(
        select(Rating).where(Rating.job_id == job_id, Rating.user_id == user.id)
    ).first()

    if not user_rating:
        raise HTTPException(status_code=404, detail="Job not found")

    if user_rating.archived:
        raise HTTPException(status_code=400, detail="Job is already archived")

    user_rating.archived = True
    db.commit()

    return {"message": "Job archived successfully"}


@job_router.post("/unarchive/{job_id}")
async def unarchive_job(
    job_id: int, user=Depends(get_user), db: Session = Depends(get_db)
):
    """
    Unarchive a job linked to your account.

    **Path Parameter:**
    - `job_id`: The unique identifier of the job to unarchive.

    **Authentication:** User must be logged in.

    **Returns:** A JSON message confirming the job has been unarchived.

    **Errors:**
    - 404 if the job (rating) is not found.
    - 400 if the job is not currently archived.
    """
    user_rating = db.exec(
        select(Rating).where(Rating.job_id == job_id, Rating.user_id == user.id)
    ).first()

    if not user_rating:
        raise HTTPException(status_code=404, detail="Job not found")

    if not user_rating.archived:
        raise HTTPException(status_code=400, detail="Job is not archived")

    user_rating.archived = False
    db.commit()

    return {"message": "Job unarchived successfully"}


class AdminJobPayload(BaseModel):
    """
    Payload for admin actions on a job.

    **Attributes:**
    - `user_id`: The ID of the user whose job rating is to be modified.
    - `job_id`: The ID of the job in question.
    """

    user_id: int
    job_id: int


@job_router.post("/sudo_archive")
async def sudo_archive_job(
    payload: AdminJobPayload, user=Depends(get_admin), db: Session = Depends(get_db)
):
    """
    Archive a job on behalf of another user (admin only).

    **Request Body:** An `AdminJobPayload` containing the user ID and job ID.

    **Authentication:** Admin privileges are required.

    **Returns:** A JSON message confirming the job has been archived.

    **Errors:**
    - 404 if the job (rating) is not found.
    - 400 if the job is already archived.
    """
    user_rating = db.exec(
        select(Rating).where(
            Rating.job_id == payload.job_id, Rating.user_id == payload.user_id
        )
    ).first()

    if not user_rating:
        raise HTTPException(status_code=404, detail="Job not found")

    if user_rating.archived:
        raise HTTPException(status_code=400, detail="Job is already archived")

    user_rating.archived = True
    db.commit()

    return {"message": "Job archived successfully"}


@job_router.post("/sudo_unarchive")
async def sudo_unarchive_job(
    payload: AdminJobPayload, user=Depends(get_admin), db: Session = Depends(get_db)
):
    """
    Unarchive a job on behalf of another user (admin only).

    **Request Body:** An `AdminJobPayload` containing the user ID and job ID.

    **Authentication:** Admin privileges are required.

    **Returns:** A JSON message confirming the job has been unarchived.

    **Errors:**
    - 404 if the job (rating) is not found.
    - 400 if the job is not archived.
    """
    user_rating = db.exec(
        select(Rating).where(
            Rating.job_id == payload.job_id, Rating.user_id == payload.user_id
        )
    ).first()

    if not user_rating:
        raise HTTPException(status_code=404, detail="Job not found")

    if not user_rating.archived:
        raise HTTPException(status_code=400, detail="Job is not archived")

    user_rating.archived = False
    db.commit()

    return {"message": "Job unarchived successfully"}


@job_router.delete("/delete/{job_id}")
async def delete_rating(
    job_id: int, user=Depends(get_user), db: Session = Depends(get_db)
):
    """
    Delete your job rating.

    **Path Parameter:**
    - `job_id`: The unique identifier of the job rating to delete.

    **Authentication:** User must be logged in.

    **Returns:** A JSON message confirming the deletion.

    **Errors:**
    - 404 if the job rating is not found.
    """
    user_rating = db.exec(
        select(Rating).where(Rating.job_id == job_id, Rating.user_id == user.id)
    ).first()

    if not user_rating:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(user_rating)
    db.commit()

    return {"message": "Job deleted successfully"}


@job_router.delete("/delete_rating")
async def sudo_delete_rating(
    user_id: int = Query(...),
    job_id: int = Query(...),
    user=Depends(get_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a job rating on behalf of another user (admin only).

    **Query Parameters:**
    - `user_id`: The ID of the user whose job rating is to be deleted.
    - `job_id`: The ID of the job rating to delete.

    **Authentication:** Admin privileges are required.

    **Returns:** A JSON message confirming the deletion.

    **Errors:**
    - 404 if the job rating is not found.
    """
    user_rating = db.exec(
        select(Rating).where(Rating.job_id == job_id, Rating.user_id == user_id)
    ).first()

    if not user_rating:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(user_rating)
    db.commit()

    return {"message": "Job deleted successfully"}


@job_router.delete("/delete_job/{job_id}")
async def sudo_delete_job(
    job_id: int, user=Depends(get_admin), db: Session = Depends(get_db)
):
    """
    Delete a job (admin only).

    **Path Parameter:**
    - `job_id`: The unique identifier of the job to delete.

    **Authentication:** Admin privileges are required.

    **Returns:** A JSON message confirming the deletion.

    **Errors:**
    - 404 if the job is not found.
    """
    job = db.exec(select(Job).where(Job.id == job_id)).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(job)
    db.commit()

    return {"message": "Job deleted successfully"}
