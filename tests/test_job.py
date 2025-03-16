import uuid
from sqlmodel import select
from data.models.job import Job
from data.models.rating import Rating
from data.models.user import User
from tests.fixtures import (
    test_client_as_admin,  # noqa: F401
    test_client_as_user,  # noqa: F401
    test_db_session,  # noqa: F401
)


def test_get_all_jobs_non_admin(test_client_as_user, test_db_session):  # noqa: F811
    """
    Ensures that only admin users can access all jobs via /jobs/all endpoint.

    - A non-admin user should receive a 403 Forbidden response.
    - The admin fixture should receive a 200 response with a list of jobs.
    """
    # Non-admin should be forbidden.
    result = test_client_as_user.get("/jobs/all")
    assert result.status_code == 403

    user = test_db_session.get(User, 1)
    user.admin = True
    test_db_session.commit()

    # Admin should be allowed.
    result = test_client_as_user.get("/jobs/all")
    assert result.status_code == 200
    assert isinstance(result.json(), list)


def test_get_mine_jobs(test_client_as_user, test_db_session):  # noqa: F811
    """
    Ensures that the /jobs/mine endpoint returns only the jobs linked to the logged-in user's ratings.

    - Inserts a job and rating for the current user (user_id=1).
    - Inserts another job and rating for a different user.
    - Verifies that only the current user's job is returned.
    """
    # Create a job and rating for current user.
    job_for_user = Job(title="Job For User", description="Desc")
    test_db_session.add(job_for_user)
    test_db_session.commit()
    test_db_session.refresh(job_for_user)
    rating_for_user = Rating(job_id=getattr(job_for_user, "id"), user_id=1)
    test_db_session.add(rating_for_user)

    # Create a job and rating for another user.
    job_for_other = Job(title="Job For Other", description="Desc")
    test_db_session.add(job_for_other)
    test_db_session.commit()
    test_db_session.refresh(job_for_other)
    rating_for_other = Rating(job_id=getattr(job_for_other, "id"), user_id=999)
    test_db_session.add(rating_for_other)
    test_db_session.commit()

    result = test_client_as_user.get("/jobs/mine")
    assert result.status_code == 200
    data = result.json()
    # Ensure only the current user's job is returned.
    assert all(job["id"] == getattr(job_for_user, "id") for job in data)


def test_get_active_and_archived_jobs(
    test_client_as_user, test_db_session  # noqa: F811
):
    """
    Ensures that the /jobs/active endpoint returns only active (not archived) jobs for the current user, and the /jobs/archived endpoint returns only archived jobs for the current user.

    - Creates an active rating and an archived rating for user_id=1.
    - Verifies that only the active job is returned with the /jobs/active endpoint.
    - Verifies that only the archived job is returned with the /jobs/archived endpoint.
    """
    # Active job.
    active_job = Job(title="Active Job", description="Desc")
    test_db_session.add(active_job)
    test_db_session.commit()
    test_db_session.refresh(active_job)
    active_rating = Rating(job_id=getattr(active_job, "id"), user_id=1, archived=False)
    test_db_session.add(active_rating)

    # Archived job.
    archived_job = Job(title="Archived Job", description="Desc")
    test_db_session.add(archived_job)
    test_db_session.commit()
    test_db_session.refresh(archived_job)
    archived_rating = Rating(
        job_id=getattr(archived_job, "id"), user_id=1, archived=True
    )
    test_db_session.add(archived_rating)
    test_db_session.commit()

    result = test_client_as_user.get("/jobs/active")
    assert result.status_code == 200
    data = result.json()
    assert len(data) == 1
    assert data[0]["id"] == getattr(active_job, "id")

    result = test_client_as_user.get("/jobs/archived")
    assert result.status_code == 200
    data = result.json()
    assert len(data) == 1
    assert data[0]["id"] == getattr(archived_job, "id")


def test_create_job_success(test_client_as_user, test_db_session):  # noqa: F811
    """
    Tests successful job creation via /jobs/create endpoint.

    - Posts a payload without an id.
    - Verifies that a job is created and linked with a rating for the current user.
    """
    payload = {
        "title": "New Job",
        "description": "Job Description",
        "company": "Test Company",
        "location": "Test City",
        "working_model": "remote",
        "salary": "100k",
        "experience_level": "mid",
        "industry": "Tech",
        "responsibilities": "Coding",
        "requirements": "Python",
        "ai_enhanced": False,
        "applicants": None,
        "posted_date": "2023-10-10",
        "pretty_url": "new-job",
        "api_url": "http://api.newjob.com",
        "iid": None,
    }
    result = test_client_as_user.post("/jobs/create", json=payload)
    assert result.status_code == 200
    message = result.json()["message"]
    assert "created" in message or "linked" in message

    # Verify job exists in DB and a rating for user_id 1 exists.
    job = test_db_session.exec(select(Job).where(Job.title == "New Job")).first()
    assert job is not None
    rating = test_db_session.exec(
        select(Rating).where(Rating.job_id == getattr(job, "id"), Rating.user_id == 1)
    ).first()
    assert rating is not None


def test_create_job_with_id_fails(test_client_as_user):  # noqa: F811
    """
    Tests that providing an id in the payload for /jobs/create results in a 400 error.
    """
    payload = {
        "id": 1,
        "title": "Job With ID",
        "description": "Job Description",
        "company": "Company",
        "location": "City",
        "working_model": "remote",
        "salary": "50k",
        "experience_level": "entry",
        "industry": "Tech",
        "responsibilities": "Testing",
        "requirements": "None",
        "ai_enhanced": False,
        "applicants": None,
        "posted_date": "2023-10-10",
        "pretty_url": "job-with-id",
        "api_url": "http://api.jobwithid.com",
        "iid": None,
    }
    result = test_client_as_user.post("/jobs/create", json=payload)
    assert result.status_code == 400


def test_create_job_duplicate_rating_fails(
    test_client_as_user, test_db_session  # noqa: F811
):
    """
    Tests that creating a job that already exists and has a rating for the user fails.

    - Uses a fixed iid so that the job is detected as a duplicate.
    """
    job_iid = str(uuid.uuid4())
    payload = {
        "title": "Duplicate Job",
        "description": "Job Description",
        "company": "Company",
        "location": "City",
        "working_model": "remote",
        "salary": "75k",
        "experience_level": "senior",
        "industry": "Tech",
        "responsibilities": "Development",
        "requirements": "Python",
        "ai_enhanced": False,
        "applicants": None,
        "posted_date": "2023-10-10",
        "pretty_url": "duplicate-job",
        "api_url": "http://api.duplicatejob.com",
        "iid": job_iid,
    }
    # Create the job the first time.
    test_client_as_user.post("/jobs/create", json=payload)
    # Try to create duplicate.
    result = test_client_as_user.post("/jobs/create", json=payload)
    assert result.status_code == 400
    assert "Job already exists" in result.json()["detail"]


def test_create_job_existing_job_without_rating(
    test_client_as_user, test_db_session  # noqa: F811
):
    """
    Tests that if a job already exists (with a given iid) but the current user has no rating for it,
    calling the /jobs/create endpoint with the same iid creates only a rating for the job and does not
    create a duplicate job.
    """
    # Pre-insert a job with a fixed iid.
    job_iid = str(uuid.uuid4())
    existing_job = Job(title="Existing Job", description="Desc", iid=job_iid)
    test_db_session.add(existing_job)
    test_db_session.commit()
    test_db_session.refresh(existing_job)

    # Ensure that no rating exists for user_id=1 for this job.
    initial_rating = test_db_session.exec(
        select(Rating).where(
            Rating.job_id == getattr(existing_job, "id"), Rating.user_id == 1
        )
    ).first()
    assert initial_rating is None

    # Prepare payload with the same iid.
    payload = {
        "title": "Existing Job",
        "description": "Desc",
        "iid": job_iid,
        "company": "Existing Company",
        "location": "Somewhere",
        "working_model": "remote",
        "salary": "100k",
        "experience_level": "mid",
        "industry": "Tech",
        "responsibilities": "None",
        "requirements": "None",
        "ai_enhanced": False,
        "applicants": None,
        "posted_date": "2023-10-10",
        "pretty_url": "existing-job",
        "api_url": "http://api.existingjob.com",
    }
    result = test_client_as_user.post("/jobs/create", json=payload)
    assert result.status_code == 200
    # Expect message indicating the job existed and is now linked to the account.
    assert "already existed and is now linked" in result.json()["message"]

    # Verify that no duplicate job was created; job count with this iid remains 1.
    jobs = test_db_session.exec(select(Job).where(Job.iid == job_iid)).all()
    assert len(jobs) == 1

    # Verify that a new rating for the current user (user_id=1) now exists.
    new_rating = test_db_session.exec(
        select(Rating).where(
            Rating.job_id == getattr(existing_job, "id"), Rating.user_id == 1
        )
    ).first()
    assert new_rating is not None


def test_archive_job_success(test_client_as_user, test_db_session):  # noqa: F811
    """
    Tests successful archiving of a job via /jobs/archive/{job_id}.

    - Creates a job and a corresponding rating for user_id=1.
    - Archives the job and verifies the rating's archived flag is set.
    """
    job = Job(title="Job to Archive", description="Desc")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    rating = Rating(job_id=getattr(job, "id"), user_id=1, archived=False)
    test_db_session.add(rating)
    test_db_session.commit()

    result = test_client_as_user.post(f"/jobs/archive/{getattr(job, 'id')}")
    assert result.status_code == 200
    assert result.json()["message"] == "Job archived successfully"

    updated_rating = test_db_session.exec(
        select(Rating).where(Rating.job_id == getattr(job, "id"), Rating.user_id == 1)
    ).first()
    assert updated_rating.archived is True


def test_archive_job_not_found(test_client_as_user):  # noqa: F811
    """
    Tests that attempting to archive a non-existent job returns a 404 error.
    """
    result = test_client_as_user.post("/jobs/archive/999999")
    assert result.status_code == 404


def test_archive_job_already_archived(
    test_client_as_user, test_db_session  # noqa: F811
):
    """
    Tests that attempting to archive an already archived job returns a 400 error.
    """
    job = Job(title="Already Archived Job", description="Desc")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    rating = Rating(job_id=getattr(job, "id"), user_id=1, archived=True)
    test_db_session.add(rating)
    test_db_session.commit()

    result = test_client_as_user.post(f"/jobs/archive/{getattr(job, 'id')}")
    assert result.status_code == 400
    assert "already archived" in result.json()["detail"]


def test_unarchive_job_success(test_client_as_user, test_db_session):  # noqa: F811
    """
    Tests successful unarchiving of a job via /jobs/unarchive/{job_id}.

    - Creates a job with an archived rating.
    - Unarchives the job and verifies the archived flag is set to False.
    """
    job = Job(title="Job to Unarchive", description="Desc")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    rating = Rating(job_id=getattr(job, "id"), user_id=1, archived=True)
    test_db_session.add(rating)
    test_db_session.commit()

    result = test_client_as_user.post(f"/jobs/unarchive/{getattr(job, 'id')}")
    assert result.status_code == 200
    assert result.json()["message"] == "Job unarchived successfully"

    updated_rating = test_db_session.exec(
        select(Rating).where(Rating.job_id == getattr(job, "id"), Rating.user_id == 1)
    ).first()
    assert updated_rating.archived is False


def test_unarchive_job_not_found(test_client_as_user):  # noqa: F811
    """
    Tests that attempting to unarchive a non-existent job returns a 404 error.
    """
    result = test_client_as_user.post("/jobs/unarchive/999999")
    assert result.status_code == 404


def test_unarchive_job_not_archived(test_client_as_user, test_db_session):  # noqa: F811
    """
    Tests that attempting to unarchive a job that is not archived returns a 400 error.
    """
    job = Job(title="Job Not Archived", description="Desc")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    rating = Rating(job_id=getattr(job, "id"), user_id=1, archived=False)
    test_db_session.add(rating)
    test_db_session.commit()

    result = test_client_as_user.post(f"/jobs/unarchive/{getattr(job, 'id')}")
    assert result.status_code == 400
    assert "not archived" in result.json()["detail"]


def test_sudo_archive_job_success(test_client_as_admin, test_db_session):  # noqa: F811
    """
    Tests that an admin can successfully archive a job via /jobs/sudo_archive.

    - Uses the admin fixture.
    - Creates a job and a rating for a different user.
    - Archives the job using admin privileges.
    """
    job = Job(title="Sudo Archive Job", description="Desc")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    rating = Rating(job_id=getattr(job, "id"), user_id=999, archived=False)
    test_db_session.add(rating)
    test_db_session.commit()

    payload = {"user_id": 999, "job_id": getattr(job, "id")}
    result = test_client_as_admin.post("/jobs/sudo_archive", json=payload)
    assert result.status_code == 200
    assert result.json()["message"] == "Job archived successfully"

    updated_rating = test_db_session.exec(
        select(Rating).where(Rating.job_id == getattr(job, "id"), Rating.user_id == 999)
    ).first()
    assert updated_rating.archived is True


def test_sudo_archive_job_not_found(
    test_client_as_admin, test_db_session  # noqa: F811
):
    """
    Tests that sudo archiving a non-existent rating returns a 404 error.
    """
    payload = {"user_id": 999, "job_id": 999999}
    result = test_client_as_admin.post("/jobs/sudo_archive", json=payload)
    assert result.status_code == 404


def test_sudo_archive_job_already_archived(
    test_client_as_admin, test_db_session  # noqa: F811
):
    """
    Tests that attempting to sudo archive an already archived job returns a 400 error.
    """
    job = Job(title="Already Sudo Archived Job", description="Desc")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    rating = Rating(job_id=getattr(job, "id"), user_id=999, archived=True)
    test_db_session.add(rating)
    test_db_session.commit()

    payload = {"user_id": 999, "job_id": getattr(job, "id")}
    result = test_client_as_admin.post("/jobs/sudo_archive", json=payload)
    assert result.status_code == 400
    assert "already archived" in result.json()["detail"]


def test_sudo_unarchive_job_success(
    test_client_as_admin, test_db_session  # noqa: F811
):
    """
    Tests that an admin can successfully unarchive a job via /jobs/sudo_unarchive.

    - Uses the admin fixture.
    - Creates a job with an archived rating for a different user.
    - Unarchives the job using admin privileges.
    """
    job = Job(title="Sudo Unarchive Job", description="Desc")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    rating = Rating(job_id=getattr(job, "id"), user_id=999, archived=True)
    test_db_session.add(rating)
    test_db_session.commit()

    payload = {"user_id": 999, "job_id": getattr(job, "id")}
    result = test_client_as_admin.post("/jobs/sudo_unarchive", json=payload)
    assert result.status_code == 200
    assert result.json()["message"] == "Job unarchived successfully"

    updated_rating = test_db_session.exec(
        select(Rating).where(Rating.job_id == getattr(job, "id"), Rating.user_id == 999)
    ).first()
    assert updated_rating.archived is False


def test_sudo_unarchive_job_not_found(
    test_client_as_admin, test_db_session  # noqa: F811
):
    """
    Tests that sudo unarchiving a non-existent rating returns a 404 error.
    """
    payload = {"user_id": 999, "job_id": 999999}
    result = test_client_as_admin.post("/jobs/sudo_unarchive", json=payload)
    assert result.status_code == 404


def test_sudo_unarchive_job_not_archived(
    test_client_as_admin, test_db_session  # noqa: F811
):
    """
    Tests that attempting to sudo unarchive a job that is not archived returns a 400 error.
    """
    job = Job(title="Sudo Not Archived Job", description="Desc")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    rating = Rating(job_id=getattr(job, "id"), user_id=999, archived=False)
    test_db_session.add(rating)
    test_db_session.commit()

    payload = {"user_id": 999, "job_id": getattr(job, "id")}
    result = test_client_as_admin.post("/jobs/sudo_unarchive", json=payload)
    assert result.status_code == 400
    assert "not archived" in result.json()["detail"]


def test_delete_rating_success(test_client_as_user, test_db_session):  # noqa: F811
    """
    Tests that a logged-in user can delete their own job rating via /jobs/delete/{job_id}.

    Steps:
    - Create a job and add it to the database.
    - Create a rating for the current user (user_id = 1) associated with that job.
    - Call the DELETE endpoint with the job's id.
    - Verify that the endpoint returns a 200 status and a confirmation message.
    - Assert that the rating no longer exists in the database.
    """
    # Create a test job.
    job = Job(title="Test Job", description="Test Description")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)

    # Create a rating for the current user (user_id=1).
    rating = Rating(job_id=getattr(job, "id"), user_id=1)
    test_db_session.add(rating)
    test_db_session.commit()

    # Call the DELETE endpoint to remove the rating.
    response = test_client_as_user.delete(f"/jobs/delete/{job.id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Job deleted successfully"}

    # Verify the rating was deleted.
    deleted_rating = test_db_session.exec(
        select(Rating).where(Rating.job_id == job.id, Rating.user_id == 1)
    ).first()
    assert deleted_rating is None


def test_delete_rating_not_found(test_client_as_user):  # noqa: F811
    """
    Tests that attempting to delete a non-existent job rating returns a 404 error.

    - Calls the DELETE endpoint with a job_id for which no rating exists.
    - Verifies that a 404 status code is returned with an appropriate error message.
    """
    response = test_client_as_user.delete("/jobs/delete/999999")
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


def test_sudo_delete_rating_success(
    test_client_as_admin, test_db_session  # noqa: F811
):
    """
    Tests that an admin can delete a job rating via /jobs/delete/rating.

    - Uses the admin fixture.
    - Creates a job and a rating for a different user.
    - Deletes the rating using admin privileges.
    """
    job = Job(title="Job for Sudo Delete Rating", description="Desc")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)
    rating = Rating(job_id=getattr(job, "id"), user_id=999)
    test_db_session.add(rating)
    test_db_session.commit()

    result = test_client_as_admin.delete(
        "/jobs/delete_rating", params={"user_id": 999, "job_id": getattr(job, "id")}
    )
    assert result.status_code == 200
    assert result.json()["message"] == "Job deleted successfully"

    remaining_rating = test_db_session.exec(
        select(Rating).where(Rating.job_id == getattr(job, "id"), Rating.user_id == 999)
    ).first()
    assert remaining_rating is None


def test_sudo_delete_rating_not_found(
    test_client_as_admin, test_db_session  # noqa: F811
):
    """
    Tests that admin deletion of a non-existent job rating returns a 404 error.
    """
    payload = {"user_id": 999, "job_id": 999999}
    result = test_client_as_admin.delete("/jobs/delete_rating", params=payload)
    assert result.status_code == 404


def test_sudo_delete_job_success(test_client_as_admin, test_db_session):  # noqa: F811
    """
    Tests that an admin can delete a job via /jobs/delete_job/{job_id}.

    - Uses the admin fixture.
    - Creates a job.
    - Deletes the job and verifies it no longer exists in the database.
    """
    job = Job(title="Job for Sudo Delete", description="Desc")
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)

    result = test_client_as_admin.delete(f"/jobs/delete_job/{getattr(job, 'id')}")
    assert result.status_code == 200
    assert result.json()["message"] == "Job deleted successfully"

    remaining_job = test_db_session.exec(
        select(Job).where(Job.id == getattr(job, "id"))
    ).first()
    assert remaining_job is None


def test_sudo_delete_job_not_found(test_client_as_admin):  # noqa: F811
    """
    Tests that admin deletion of a non-existent job returns a 404 error.
    """
    result = test_client_as_admin.delete("/jobs/delete_job/999999")
    assert result.status_code == 404


def test_sudo_archive_forbidden(test_client_as_user):  # noqa: F811
    """
    Tests that a non-admin user is forbidden from accessing the sudo_archive endpoint.
    """
    # Use a dummy payload.
    payload = {"user_id": 999, "job_id": 1}
    result = test_client_as_user.post("/jobs/sudo_archive", json=payload)
    assert result.status_code == 403


def test_sudo_unarchive_forbidden(test_client_as_user):  # noqa: F811
    """
    Tests that a non-admin user is forbidden from accessing the sudo_unarchive endpoint.
    """
    # Use a dummy payload.
    payload = {"user_id": 999, "job_id": 1}
    result = test_client_as_user.post("/jobs/sudo_unarchive", json=payload)
    assert result.status_code == 403


def test_sudo_delete_rating_forbidden(test_client_as_user):  # noqa: F811
    """
    Tests that a non-admin user is forbidden from accessing the sudo_delete_rating endpoint.
    """
    # Use dummy query parameters.
    result = test_client_as_user.delete(
        "/jobs/delete_rating", params={"user_id": 999, "job_id": 1}
    )
    assert result.status_code == 403


def test_sudo_delete_job_forbidden(test_client_as_user):  # noqa: F811
    """
    Tests that a non-admin user is forbidden from accessing the sudo_delete_job endpoint.
    """
    result = test_client_as_user.delete("/jobs/delete_job/1")
    assert result.status_code == 403
