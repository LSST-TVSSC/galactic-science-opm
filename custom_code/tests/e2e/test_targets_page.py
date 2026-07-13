import filecmp
import os
import re
from playwright.sync_api import Page, expect
import pytest
from custom_code.tests.e2e.data.test_data import BASE_URL, TEST_TARGETS, VALID_USER_CREDENTIALS
from custom_code.tests.e2e.pages.targets_page import TargetsPage

NUMBER_OF_ELEMENTS_PER_PAGE_UNAUTH = 1
NUMBER_OF_ELEMENTS_PER_PAGE = 20
NUMBER_OF_ELEMENTS_TOTAL = 40
TARGET_GROUP_NAME = "TEST-GROUP"

def test_unauthorized_user_can_not_view_page(page: Page):
    LOGIN_REQUEST_TEXT = "Please login to view or create targets."

    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()

    targets_table_container = page.get_by_test_id("targets-table")
    targets_table = targets_table_container.locator("table")
    target_rows = targets_table.locator("tbody tr")

    expect(target_rows).to_have_count(
        NUMBER_OF_ELEMENTS_PER_PAGE_UNAUTH
    )
    expect(targets_table).to_contain_text(re.compile(fr".*{LOGIN_REQUEST_TEXT}"))

def test_authorized_user_can_view_page(page: Page):

    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)

    targets_table_container = page.get_by_test_id("targets-table")
    skymap_container = page.get_by_test_id("skymap")

    targets_table = targets_table_container.locator("table")
    target_rows = targets_table.locator("tbody tr")
    targets_pagination = page.get_by_test_id("pagination-top")

    expect(target_rows).to_have_count(
        NUMBER_OF_ELEMENTS_PER_PAGE
    )
    expect(targets_pagination).to_contain_text(re.compile(rf"of {NUMBER_OF_ELEMENTS_TOTAL}"))

    for row in TEST_TARGETS:
        name, target_type, obs, saved, pk = row['name'], row['type'], row['obs'], row['saved'], row['pk'] 
        expect(targets_table).to_contain_text(re.compile(rf"{name}\s+{target_type}\s+{obs}\s+{saved}\s+"))
        link_for_test_target = targets_table.get_by_role("link", name=str(name))
        expect(link_for_test_target).to_have_attribute("href", f"/targets/{pk}/")

    # coupling is a bit tight: selects canvas...
    expect(skymap_container.locator("canvas").first).to_be_visible()

def test_authorized_user_can_search(page: Page):
    TARGET = TEST_TARGETS[0]
    NUMBER_OF_RESULTS = 1
    name, target_type, obs, saved, pk = TARGET['name'], TARGET['type'], TARGET['obs'], TARGET['saved'], TARGET['pk'] 
    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)
    target_page.filter(name)

    targets_table_container = page.get_by_test_id("targets-table")
    targets_table = targets_table_container.locator("table")
    target_rows = targets_table.locator("tbody tr")
    targets_pagination = page.get_by_test_id("pagination-top")

    expect(target_rows).to_have_count(NUMBER_OF_RESULTS)
    expect(targets_pagination).to_contain_text(re.compile(rf"of {NUMBER_OF_RESULTS}"))

    expect(targets_table).to_contain_text(re.compile(rf"{name}\s+{target_type}\s+{obs}\s+{saved}\s+"))
    link_for_test_target = targets_table.get_by_role("link", name=str(name))
    expect(link_for_test_target).to_have_attribute("href", f"/targets/{pk}/")

def test_authorized_user_sees_no_results_text_unknown_name(page: Page):
    NO_RESULTS_TEXT = "No targets match those filters."
    NON_EXISTENT_TARGET = "Hoth" 
    NUMBER_OF_ROWS = 1
    NUMBER_OF_RESULTS = 0

    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)
    target_page.filter(NON_EXISTENT_TARGET)

    targets_table_container = page.get_by_test_id("targets-table")
    targets_table = targets_table_container.locator("table")
    target_rows = targets_table.locator("tbody tr")
    targets_pagination = page.get_by_test_id("pagination-top")

    expect(target_rows).to_have_count(NUMBER_OF_ROWS)
    expect(targets_pagination).to_contain_text(re.compile(rf"of {NUMBER_OF_RESULTS}"))

    expect(targets_table).to_contain_text(re.compile(rf"{NO_RESULTS_TEXT}"))

def test_authorized_user_sees_can_reset_form(page: Page):
    NO_RESULTS_TEXT = "No targets match those filters."
    NON_EXISTENT_TARGET = "Hoth" 
    NUMBER_OF_ROWS = 1
    NUMBER_OF_RESULTS = 0

    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)
    target_page.filter(NON_EXISTENT_TARGET)

    targets_table_container = page.get_by_test_id("targets-table")
    targets_table = targets_table_container.locator("table")
    target_rows = targets_table.locator("tbody tr")
    targets_pagination = page.get_by_test_id("pagination-top")

    expect(target_rows).to_have_count(NUMBER_OF_ROWS)
    expect(targets_pagination).to_contain_text(re.compile(rf"of {NUMBER_OF_RESULTS}"))

    expect(targets_table).to_contain_text(re.compile(rf"{NO_RESULTS_TEXT}"))

    target_page.reset()

    expect(target_rows).to_have_count(NUMBER_OF_ELEMENTS_PER_PAGE)
    expect(target_page.get_filter_field("Name")).to_be_empty()

def test_authorized_user_can_create_target(page: Page):
    NON_EXISTENT_TARGET = "Hoth" 
    NON_EXISTENT_RA = 201
    NON_EXISTENT_DEC = 11 

    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)
    target_page.create_target(name=NON_EXISTENT_TARGET, ra=NON_EXISTENT_RA, dec=NON_EXISTENT_DEC)

    expect(page).to_have_title(re.compile(fr".*{NON_EXISTENT_TARGET}"))

def test_authorized_user_can_merge_targets(page: Page):
    TO_MERGE = [t['name'] for t in TEST_TARGETS]

    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)
    target_page.merge_targets(*TO_MERGE)

    expect(page).to_have_title(re.compile(fr".*{TO_MERGE[0]}"))

    target_info = page.get_by_test_id("target-info")
    for m in TO_MERGE:
        expect(target_info).to_contain_text(re.compile(fr".*{m}"))

def test_authorized_user_can_upload_targets(page: Page):
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    TARGETS_CSV_PATH = os.path.join(BASE_PATH, "data", "target_import.csv")

    NUMBER_OF_TARGETS_IN_CSV = 2
    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)

    target_page.upload_targets(TARGETS_CSV_PATH)
    message_container = (page.get_by_text(f"Targets created: {NUMBER_OF_TARGETS_IN_CSV}"))
    expect(message_container).to_be_visible()

@pytest.mark.skip(reason="Was removed from tomtoolkit it seems")
def test_authorized_user_can_search_catalogs(page: Page):
    SEARCH_TERM = "FOO"
    CATALOG = "Simbad"
    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)

    target_page.query_catalog(SEARCH_TERM, CATALOG)
    message_container = (page.get_by_text(f"Object not found"))
    expect(message_container).to_be_visible()

@pytest.mark.skip(reason="Was removed from tomtoolkit in commit 28490ac")
def test_authorized_user_update_broker_data(page: Page):
    
    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)

    target_page.update_broker_data()
    message_container = page.get_by_text("Update completed successfully")
    expect(message_container).to_be_visible()

def test_authorized_user_export_data(page: Page):

    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    EXPECTED_CSV = os.path.join(BASE_PATH, "data", "expected_export.csv")
    TARGET_TO_FILTER = "ZTF24abshzkw"
    
    target_page = TargetsPage(page, BASE_URL)
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)
    target_page.filter(TARGET_TO_FILTER)

    path_actual_csv = target_page.export_data()
    result = (filecmp.cmp(path_actual_csv, EXPECTED_CSV))
    assert result
    os.remove(path_actual_csv)
        
