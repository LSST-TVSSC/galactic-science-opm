import re
from playwright.sync_api import Page, expect

from custom_code.tests.e2e.data.test_data import BASE_URL, VALID_USER_CREDENTIALS
from custom_code.tests.e2e.pages.alerts_page import AlertsPage

"""
Since this is a module provided by tomtoolkit, the testing done here
should be minimal.
"""

def test_alerts_page_is_not_available_to_anonymous_user(page: Page):

    alerts_page = AlertsPage(page, BASE_URL)
    alerts_page.open_it()

    expect(page).to_have_title(re.compile(r".*Login"))

def test_alerts_page_is_available_to_authenticated_user__no_content(page: Page):
    NO_RESULTS_TEXT = (
        "No saved queries yet, Try creating a query from "
        "one of the alert brokers listed above."
    )
    alerts_page = AlertsPage(page, BASE_URL)
    alerts_page.open_it()
    alerts_page.login(*VALID_USER_CREDENTIALS)

    query_table = alerts_page.get_query_table()
    expect(page).to_have_title(re.compile(r".*Query List"))
    expect(query_table).to_contain_text(re.compile(fr"{NO_RESULTS_TEXT}"))

def test_authenticated_user_can_create_query(page: Page):
    TARGET_NAME = "ZTF26aaousvi"
    QUERY_NAME = "my-query"
    alerts_page = AlertsPage(page, BASE_URL)
    alerts_page.open_it()
    alerts_page.login(*VALID_USER_CREDENTIALS)

    alerts_page.create_query(QUERY_NAME, TARGET_NAME)

    query_table = alerts_page.get_query_table()
    expect(page).to_have_title(re.compile(r".*Query List"))
    expect(query_table.get_by_role("cell", name=QUERY_NAME)).to_be_visible()

def test_authenticated_user_can_filter_query(page: Page):
    TARGET_NAME = "ZTF26aaousvi"
    QUERY_NAME = "my-query"
    QUERY_NAME_OTHER = "your-query"
    alerts_page = AlertsPage(page, BASE_URL)
    alerts_page.open_it()
    alerts_page.login(*VALID_USER_CREDENTIALS)

    alerts_page.create_query(QUERY_NAME, TARGET_NAME)
    alerts_page.create_query(QUERY_NAME_OTHER, TARGET_NAME)

    alerts_page.filter_query("ALeRCE", QUERY_NAME_OTHER)

    query_table = alerts_page.get_query_table()
    expect(page).to_have_title(re.compile(r".*Query List"))
    expect(query_table.get_by_role("cell", name=QUERY_NAME)).not_to_be_visible()
    expect(query_table.get_by_role("cell", name=QUERY_NAME_OTHER)).to_be_visible()

def test_authenticated_user_sees_no_results_page(page: Page):
    NO_RESULTS_TEXT = (
        "No saved queries yet, "
        "Try creating a query from one of the alert brokers listed above."
    ) 

    TARGET_NAME = "ZTF26aaousvi"
    QUERY_NAME = "my-other-query"
    QUERY_NAME_FILTER = "none"
    alerts_page = AlertsPage(page, BASE_URL)
    alerts_page.open_it()
    alerts_page.login(*VALID_USER_CREDENTIALS)

    alerts_page.create_query(QUERY_NAME, TARGET_NAME)

    alerts_page.filter_query("ALeRCE", QUERY_NAME_FILTER)

    query_table = alerts_page.get_query_table()
    expect(page).to_have_title(re.compile(r".*Query List"))
    expect(query_table).to_contain_text(NO_RESULTS_TEXT)




