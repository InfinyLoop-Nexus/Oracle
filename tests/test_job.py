from sqlmodel import select
from data.models.rating import Rating
from data.models.user import User
from data.models.job import Job
from tests.fixtures import test_client_as_user, test_db_session  # noqa: F401
from datetime import datetime, timedelta


def test_read_all_jobs_admin_only(test_client_as_user, test_db_session):  # noqa: F811
    """Ensures only admins can access all jobs."""
    result = test_client_as_user.get("/jobs/all")
    assert result.status_code == 403  # Non-admin should be forbidden

    user = test_db_session.get(User, 1)
    user.admin = True
    test_db_session.commit()

    result = test_client_as_user.get("/jobs/all")
    assert result.status_code == 200  # Admin should be able to access


def test_read_my_jobs(test_client_as_user, test_db_session):  # noqa: F811
    """Ensures only the logged-in user's jobs are returned via ratings."""
    # Create a job that will be linked to user with ID 1 via a Rating.
    user_job = Job(
        title="Engineer",
        description="Job description",
        posted_date="2023-10-10",
        working_model="remote",
        location="NY",
    )
    another_user_job = Job(
        title="Technician",
        description="Other job description",
        posted_date="2023-10-10",
        working_model="office",
        location="LA",
    )
    test_db_session.add(user_job)
    test_db_session.add(another_user_job)
    test_db_session.commit()
    test_db_session.refresh(user_job)
    test_db_session.refresh(another_user_job)

    # Create Rating linking the job to user 1.
    user_rating = Rating(
        job_id=user_job.id,
        user_id=1,
        user_rated=True,
        user_rating=4.5,
    )
    test_db_session.add(user_rating)

    # Create Rating linking the other job to another user.
    another_user_rating = Rating(
        job_id=another_user_job.id,
        user_id=999,
        user_rated=True,
        user_rating=3.8,
    )
    test_db_session.add(another_user_rating)
    test_db_session.commit()

    result = test_client_as_user.get("/jobs/mine")
    assert result.status_code == 200

    result_data = result.json()
    # Verify that only jobs linked to user 1 are returned.
    assert len(result_data) == 1
    assert result_data[0]["id"] == user_job.id

def test_create_job(test_client_as_user, test_db_session):  # noqa: F811
    """Tests if a job can be successfully created and persisted in DB."""
    payload = {
        "title": "Engineer",
        "description": "Job description",
        "posted_date": "2023-10-10",
        "working_model": "remote",
        "location": "NY",
        "user_id": 1,
    }
    result = test_client_as_user.post("/jobs/create", json=payload)
    assert result.status_code == 200
    assert result.json() == {"message": "Job created successfully"}

    job_exists = test_db_session.execute(
        select(Job).where(Job.title == "Engineer")
    ).scalar_one_or_none()
    assert job_exists is not None

    assert job_exists.created_at is not None
    assert job_exists.updated_at is not None

    now = datetime.now()
    assert now - timedelta(minutes=1) <= job_exists.created_at <= now
    assert now - timedelta(minutes=1) <= job_exists.updated_at <= now


def test_update_job_updates_timestamp(test_client_as_user, test_db_session):  # noqa: F811
    """Tests if updating a job automatically updates the updated_at field."""
    job = Job(
        user_id=1,
        title="Engineer",
        description="Job description",
        posted_date="2023-10-10",
        working_model="remote",
        location="NY",
    )
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)

    initial_updated_at = job.updated_at

    payload = {
        "id": job.id,
        "user_id": job.user_id,
        "title": "Senior Engineer",
        "description": job.description,
        "posted_date": job.posted_date,
        "working_model": job.working_model,
    }

    result = test_client_as_user.post("/jobs/update", json=payload)
    assert result.status_code == 200

    test_db_session.expire_all()
    updated_job = test_db_session.get(Job, job.id)
    # Check that the title has been updated and assume updated_at is refreshed.
    assert updated_job.title == "Senior Engineer"
    assert updated_job.updated_at > initial_updated_at, "updated_at should be updated on modification"


def test_create_job_with_id_fails(test_client_as_user, test_db_session):  # noqa: F811
    payload = {
        "id": 1,
        "title": "Engineer",
        "description": "Job description",
        "posted_date": "2023-10-10",
        "working_model": "remote",
        "location": "NY",
        "user_id": 1,
    }
    result = test_client_as_user.post("/jobs/create", json=payload)
    assert result.status_code == 400


def test_create_job_for_another_user_fails(test_client_as_user, test_db_session):  # noqa: F811
    payload = {
        "user_id": 999,
        "title": "Engineer",
        "description": "Job description",
        "posted_date": "2023-10-10",
        "working_model": "remote",
        "location": "NY",
    }
    result = test_client_as_user.post("/jobs/create", json=payload)
    assert result.status_code == 403


def test_admin_can_create_job_for_others(test_client_as_user, test_db_session):  # noqa: F811
    """Ensures an admin can create jobs for other users."""
    user = test_db_session.get(User, 1)
    user.admin = True
    test_db_session.commit()

    payload = {
        "user_id": 999,
        "title": "Admin Job",
        "description": "Job description",
        "posted_date": "2023-10-10",
        "working_model": "remote",
        "location": "SF",
    }
    result = test_client_as_user.post("/jobs/create", json=payload)
    assert result.status_code == 200

    test_db_session.expire_all()
    job_exists = test_db_session.execute(
        select(Job).where(Job.user_id == 999)
    ).scalar_one_or_none()
    assert job_exists is not None


def test_update_own_job(test_client_as_user, test_db_session):  # noqa: F811
    """Ensures a user can update their own job and persist the changes."""
    job = Job(
        user_id=1,
        title="Original Title",
        description="Job description",
        posted_date="2023-10-10",
        working_model="remote",
        location="NY",
    )
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)

    payload = {
        "id": job.id,
        "user_id": job.user_id,
        "title": "Updated Title",
        "description": job.description,
        "posted_date": job.posted_date,
        "working_model": job.working_model,
    }

    result = test_client_as_user.post("/jobs/update", json=payload)
    assert result.status_code == 200
    assert result.json() == {"message": "Job updated successfully"}

    test_db_session.expire_all()
    updated_job = test_db_session.get(Job, job.id)
    assert updated_job.title == "Updated Title"


def test_update_job_without_id_fails(test_client_as_user, test_db_session):  # noqa: F811
    payload = {
        "title": "Updated Title",
        "description": "Job description",
        "posted_date": "2023-10-10",
        "working_model": "remote",
    }
    result = test_client_as_user.post("/jobs/update", json=payload)
    assert result.status_code == 400


def test_update_nonexistent_job_fails(test_client_as_user, test_db_session):  # noqa: F811
    payload = {
        "id": 999,
        "title": "Updated Title",
        "description": "Job description",
        "posted_date": "2023-10-10",
        "working_model": "remote",
    }
    result = test_client_as_user.post("/jobs/update", json=payload)
    assert result.status_code == 404


def test_update_job_for_another_user_fails(test_client_as_user, test_db_session):  # noqa: F811
    job = Job(
        user_id=999,
        title="User Job",
        description="Job description",
        posted_date="2023-10-10",
        working_model="office",
        location="LA",
    )
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)

    payload = {
        "id": job.id,
        "user_id": job.user_id,
        "title": "Admin Updated",
        "description": job.description,
        "posted_date": job.posted_date,
        "working_model": job.working_model,
    }

    result = test_client_as_user.post("/jobs/update", json=payload)
    assert result.status_code == 403


def test_admin_can_update_other_users_job(test_client_as_user, test_db_session):  # noqa: F811
    """Ensures an admin can update another user's job."""
    user = test_db_session.get(User, 1)
    user.admin = True
    test_db_session.commit()

    job = Job(
        user_id=999,
        title="User Job",
        description="Job description",
        posted_date="2023-10-10",
        working_model="office",
        location="LA",
    )
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)

    payload = {
        "id": job.id,
        "user_id": job.user_id,
        "title": "Admin Updated",
        "description": job.description,
        "posted_date": job.posted_date,
        "working_model": job.working_model,
    }

    result = test_client_as_user.post("/jobs/update", json=payload)
    assert result.status_code == 200

    test_db_session.expire_all()
    updated_job = test_db_session.get(Job, job.id)
    assert updated_job.title == "Admin Updated"


def test_admin_can_delete_other_users_job(test_client_as_user, test_db_session):  # noqa: F811
    """Ensures an admin can delete another user's job."""
    user = test_db_session.get(User, 1)
    user.admin = True
    test_db_session.commit()

    job = Job(
        user_id=999,
        title="To be deleted",
        description="Job description",
        posted_date="2023-10-10",
        working_model="remote",
        location="NY",
    )
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)

    job_id = job.id

    result = test_client_as_user.delete(f"/jobs/delete/{job_id}")
    assert result.status_code == 200
    assert result.json() == {"message": "Job deleted successfully"}

    test_db_session.expire_all()
    job_exists = test_db_session.execute(
        select(Job.id).where(Job.id == job_id)
    ).scalar_one_or_none()

    assert job_exists is None


def test_delete_own_job(test_client_as_user, test_db_session):  # noqa: F811
    """Ensures a user can delete their own job."""
    job = Job(
        user_id=1,
        title="To be deleted",
        description="Job description",
        posted_date="2023-10-10",
        working_model="remote",
        location="NY",
    )
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)

    job_id = job.id

    result = test_client_as_user.delete(f"/jobs/delete/{job_id}")
    assert result.status_code == 200
    assert result.json() == {"message": "Job deleted successfully"}

    test_db_session.expire_all()
    job_exists = test_db_session.execute(
        select(Job.id).where(Job.id == job_id)
    ).scalar_one_or_none()

    assert job_exists is None


def test_delete_nonexistent_job_fails(test_client_as_user, test_db_session):  # noqa: F811
    result = test_client_as_user.delete("/jobs/delete/999")
    assert result.status_code == 404


def test_delete_job_for_another_user_fails(test_client_as_user, test_db_session):  # noqa: F811
    job = Job(
        user_id=999,
        title="To be deleted",
        description="Job description",
        posted_date="2023-10-10",
        working_model="remote",
        location="NY",
    )
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)

    job_id = job.id

    result = test_client_as_user.delete(f"/jobs/delete/{job_id}")
    assert result.status_code == 403