from sqlmodel import select
from data.models.user import User
from data.models.search import Search
from tests.fixtures import test_client_as_user, test_db_session  # noqa: F401


def test_read_all_searches_admin_only(
    test_client_as_user, test_db_session  # noqa: F811
):
    """Ensures only admins can access all searches."""
    result = test_client_as_user.get("/search/read_all")
    assert result.status_code == 403  # Non-admin should be forbidden

    user = test_db_session.get(User, 1)
    user.admin = True
    test_db_session.commit()

    result = test_client_as_user.get("/search/read_all")
    assert result.status_code == 200  # Admin should be able to access


def test_read_my_searches(test_client_as_user, test_db_session):  # noqa: F811
    """Ensures only the logged-in user's searches are returned."""
    user_search = Search(
        user_id=1,
        job_title="title1",
        date_posted="2023-10-10",
        working_model="remote",
        location="NY",
        scraping_amount=5,
        platform="LinkedIn",
    )
    another_user_search = Search(
        user_id=999,
        job_title="title2",
        date_posted="2023-10-10",
        working_model="office",
        location="LA",
        scraping_amount=2,
        platform="Indeed",
    )

    test_db_session.add(user_search)
    test_db_session.add(another_user_search)
    test_db_session.commit()
    test_db_session.refresh(user_search)

    result = test_client_as_user.get("/search/read")
    assert result.status_code == 200

    result_data = result.json()
    assert len(result_data) == 1
    assert result_data[0]["user_id"] == 1  # Should only return searches for user 1


def test_create_search(test_client_as_user, test_db_session):  # noqa: F811
    """Tests if a search can be successfully created and persisted in DB."""
    payload = {
        "job_title": "Engineer",
        "date_posted": "2023-10-10",
        "working_model": "remote",
        "location": "NY",
        "scraping_amount": 5,
        "platform": "LinkedIn",
        "user_id": 1,
    }
    result = test_client_as_user.post("/search/create", json=payload)
    assert result.status_code == 200
    assert result.json() == {"message": "Search created successfully"}

    search_exists = test_db_session.execute(
        select(Search).where(Search.job_title == "Engineer")
    ).scalar_one_or_none()
    assert search_exists is not None


def test_create_search_with_id_fails(
    test_client_as_user, test_db_session  # noqa: F811
):
    payload = {
        "id": 1,
        "job_title": "Engineer",
        "date_posted": "2023-10-10",
        "working_model": "remote",
        "location": "NY",
        "scraping_amount": 5,
        "platform": "LinkedIn",
        "user_id": 1,
    }
    result = test_client_as_user.post("/search/create", json=payload)
    assert result.status_code == 400


def test_create_search_for_another_user_fails(
    test_client_as_user, test_db_session  # noqa: F811
):
    payload = {
        "user_id": 999,
        "job_title": "Engineer",
        "date_posted": "2023-10-10",
        "working_model": "remote",
        "location": "NY",
        "scraping_amount": 5,
        "platform": "LinkedIn",
    }
    result = test_client_as_user.post("/search/create", json=payload)
    assert result.status_code == 403


def test_admin_can_create_search_for_others(
    test_client_as_user, test_db_session  # noqa: F811
):
    """Ensures an admin can create searches for other users."""
    user = test_db_session.get(User, 1)
    user.admin = True
    test_db_session.commit()

    payload = {
        "user_id": 999,
        "job_title": "Admin Job",
        "date_posted": "2023-10-10",
        "working_model": "remote",
        "location": "SF",
        "scraping_amount": 3,
        "platform": "Indeed",
    }
    result = test_client_as_user.post("/search/create", json=payload)
    assert result.status_code == 200

    test_db_session.expire_all()
    search_exists = test_db_session.execute(
        select(Search).where(Search.user_id == 999)
    ).scalar_one_or_none()
    assert search_exists is not None


def test_update_own_search(test_client_as_user, test_db_session):  # noqa: F811
    """Ensures a user can update their own search and persist the changes."""
    search = Search(
        user_id=1,
        job_title="Original Title",
        date_posted="2023-10-10",
        working_model="remote",
        location="NY",
        scraping_amount=5,
        platform="LinkedIn",
    )
    test_db_session.add(search)
    test_db_session.commit()
    test_db_session.refresh(search)

    payload = {
        "id": search.id,
        "user_id": search.user_id,
        "job_title": "Updated Title",
        "date_posted": search.date_posted,
        "working_model": search.working_model,
    }

    result = test_client_as_user.post("/search/update", json=payload)
    assert result.status_code == 200
    assert result.json() == {"message": "Search updated successfully"}

    test_db_session.expire_all()
    updated_search = test_db_session.get(Search, search.id)
    assert updated_search.job_title == "Updated Title"


def test_update_search_without_id_fails(
    test_client_as_user, test_db_session  # noqa: F811
):
    payload = {
        "job_title": "Updated Title",
        "date_posted": "2023-10-10",
        "working_model": "remote",
    }
    result = test_client_as_user.post("/search/update", json=payload)
    assert result.status_code == 400


def test_update_nonexistent_search_fails(
    test_client_as_user, test_db_session  # noqa: F811
):
    payload = {
        "id": 999,
        "job_title": "Updated Title",
        "date_posted": "2023-10-10",
        "working_model": "remote",
    }
    result = test_client_as_user.post("/search/update", json=payload)
    assert result.status_code == 404


def test_update_search_for_another_user_fails(
    test_client_as_user, test_db_session  # noqa: F811
):
    search = Search(
        user_id=999,
        job_title="User Job",
        date_posted="2023-10-10",
        working_model="office",
        location="LA",
        scraping_amount=2,
        platform="Indeed",
    )
    test_db_session.add(search)
    test_db_session.commit()
    test_db_session.refresh(search)

    payload = {
        "id": search.id,
        "user_id": search.user_id,
        "job_title": "Admin Updated",
        "date_posted": search.date_posted,
        "working_model": search.working_model,
    }

    result = test_client_as_user.post("/search/update", json=payload)
    assert result.status_code == 403


def test_admin_can_update_other_users_search(
    test_client_as_user, test_db_session  # noqa: F811
):
    """Ensures an admin can update another user's search."""
    user = test_db_session.get(User, 1)
    user.admin = True
    test_db_session.commit()

    search = Search(
        user_id=999,
        job_title="User Job",
        date_posted="2023-10-10",
        working_model="office",
        location="LA",
        scraping_amount=2,
        platform="Indeed",
    )
    test_db_session.add(search)
    test_db_session.commit()
    test_db_session.refresh(search)

    payload = {
        "id": search.id,
        "user_id": search.user_id,
        "job_title": "Admin Updated",
        "date_posted": search.date_posted,
        "working_model": search.working_model,
    }

    result = test_client_as_user.post("/search/update", json=payload)
    assert result.status_code == 200

    # ✅ Ensure update is persisted
    test_db_session.expire_all()
    updated_search = test_db_session.get(Search, search.id)
    assert updated_search.job_title == "Admin Updated"


def test_admin_can_delete_other_users_search(
    test_client_as_user, test_db_session  # noqa: F811
):
    """Ensures an admin can delete another user's search."""
    user = test_db_session.get(User, 1)
    user.admin = True
    test_db_session.commit()

    search = Search(
        user_id=999,
        job_title="To be deleted",
        date_posted="2023-10-10",
        working_model="remote",
        location="NY",
        scraping_amount=5,
        platform="LinkedIn",
    )
    test_db_session.add(search)
    test_db_session.commit()
    test_db_session.refresh(search)

    search_id = search.id

    result = test_client_as_user.delete(f"/search/delete/{search_id}")
    assert result.status_code == 200
    assert result.json() == {"message": "Search deleted successfully"}

    test_db_session.expire_all()
    search_exists = test_db_session.execute(
        select(Search.id).where(Search.id == search_id)
    ).scalar_one_or_none()

    assert search_exists is None


def test_delete_own_search(test_client_as_user, test_db_session):  # noqa: F811
    """Ensures a user can delete their own search."""
    search = Search(
        user_id=1,
        job_title="To be deleted",
        date_posted="2023-10-10",
        working_model="remote",
        location="NY",
        scraping_amount=5,
        platform="LinkedIn",
    )
    test_db_session.add(search)
    test_db_session.commit()
    test_db_session.refresh(search)

    search_id = search.id

    result = test_client_as_user.delete(f"/search/delete/{search_id}")
    assert result.status_code == 200
    assert result.json() == {"message": "Search deleted successfully"}

    test_db_session.expire_all()
    search_exists = test_db_session.execute(
        select(Search.id).where(Search.id == search_id)
    ).scalar_one_or_none()

    assert search_exists is None


def test_delete_nonexistent_search_fails(
    test_client_as_user, test_db_session  # noqa: F811
):
    result = test_client_as_user.delete("/search/delete/999")
    assert result.status_code == 404


def test_delete_search_for_another_user_fails(
    test_client_as_user, test_db_session  # noqa: F811
):
    search = Search(
        user_id=999,
        job_title="To be deleted",
        date_posted="2023-10-10",
        working_model="remote",
        location="NY",
        scraping_amount=5,
        platform="LinkedIn",
    )
    test_db_session.add(search)
    test_db_session.commit()
    test_db_session.refresh(search)

    search_id = search.id

    result = test_client_as_user.delete(f"/search/delete/{search_id}")
    assert result.status_code == 403
