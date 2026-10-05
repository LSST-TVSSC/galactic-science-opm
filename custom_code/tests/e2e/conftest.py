import os

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def flush_db_and_seed_e2e_data():
    """
    Fixture that runs at the beginning of E2E test to reset the database.
    Will fail if endpoint is not available.
    """
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    response = requests.get(
        BASE_URL + ("/flush_and_seed"),
        headers={"X-Test-Auth": os.getenv("TEST_ENDPOINT_SECRET", None)},
    )
    if response.status_code != 201:
        raise Exception(  # noqa: TRY002
            "/flush_and_seed failed. Maybe the endpoint does not exist? "
            "Is the dump in the right folder? Cancelling tests. Run in E2E setup."
        )

    yield
