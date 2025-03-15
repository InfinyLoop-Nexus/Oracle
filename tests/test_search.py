from data.models.user import User
from data.models.search import Search
from tests.fixtures import test_client_as_user, test_db_session  # noqa: F401
from tests.helpers import assert_dictionaries_are_equal_except


def test_all_searches_should_only_be_available_to_admin(
    test_client_as_user, test_db_session # noqa: F811
):  # noqa: F811
    result = test_client_as_user.get("/search/")
    assert result.status_code == 403

    user = test_db_session.get(User, 1)
    user.admin = True
    test_db_session.commit()

    result = test_client_as_user.get("/search/")
    assert result.status_code == 200


def test_search_mine_should_only_return_current_user_searches(
    test_client_as_user, test_db_session # noqa: F811
):
    user1_search = Search(
        user_id=1,
        job_title="title1",
        date_posted="date1",
        working_model="model1",
        location="location1",
        scraping_amount=1,
        platform="platform1",
    )
    user2_search = Search(
        user_id=2,
        job_title="title2",
        date_posted="date2",
        working_model="model2",
        location="location2",
        scraping_amount=2,
        platform="platform2",
    )

    test_db_session.add(user1_search)
    test_db_session.add(user2_search)
    test_db_session.commit()
    test_db_session.refresh(user1_search)

    result = test_client_as_user.get("/search/mine")
    assert result.status_code == 200
    result = result.json()

    assert_dictionaries_are_equal_except(result[0], user1_search.model_dump(), ["created_at", "updated_at"])

def test_upsert_search_create(test_client_as_user, test_db_session): # noqa: F811
    payload = {
        "job_title": "Engineer",
        "date_posted": "2023-10-10",
        "working_model": "remote",
        "location": "NY",
        "scraping_amount": 5,
        "platform": "LinkedIn"
    }
    result = test_client_as_user.post("/search/", json=payload)
    assert result.status_code == 200

    result = result.json()
    assert result["user_id"] == 1
    assert result["id"] == 1
    assert_dictionaries_are_equal_except(result, payload, ["created_at", "updated_at", "id", "user_id"])

def test_upsert_search_update_own(test_client_as_user, test_db_session): # noqa: F811
    # create a search record assigned to the current user (assumed id=1)
    search = Search(
        user_id=1,
        job_title="Original",
        date_posted="2023-10-10",
        working_model="remote",
        location="NY",
        scraping_amount=5,
        platform="LinkedIn"
    )
    test_db_session.add(search)
    test_db_session.commit()
    test_db_session.refresh(search)

    search.job_title = "Updated"

    result = test_client_as_user.post("/search/update", json=search.model_dump_json())
    assert result.status_code == 200
    data = result.json()
    assert data["job_title"] == "Updated"


def test_upsert_search_update_forbidden(test_client_as_user, test_db_session): # noqa: F811
    # create a search record assigned to a different user (e.g. user_id=999)
    search = Search(
        user_id=999,
        job_title="Not Yours",
        date_posted="2023-10-10",
        working_model="office",
        location="LA",
        scraping_amount=2,
        platform="Indeed"
    )
    test_db_session.add(search)
    test_db_session.commit()
    test_db_session.refresh(search)

    payload = search.model_dump()
    payload["job_title"] = "Attempt update"
    result = test_client_as_user.post("/search/", json=payload)
    assert result.status_code == 403
