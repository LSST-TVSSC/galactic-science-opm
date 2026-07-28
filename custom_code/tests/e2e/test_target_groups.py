import re
from playwright.sync_api import Page, expect
import pytest

from custom_code.tests.e2e.data.test_data import BASE_URL, VALID_ADMIN_CREDENTIALS, VALID_USER_CREDENTIALS
from custom_code.tests.e2e.pages.target_grouping import TargetGroupingPage

NUMBER_OF_ELEMENTS_PER_PAGE_UNAUTH = 1
NUMBER_OF_ELEMENTS_PER_PAGE = 20
NUMBER_OF_ELEMENTS_TOTAL = 40
TARGET_GROUP_NAME = "TEST-GROUP"

def test_unauthorized_user_can_not_create_target_groups(page: Page):

    target_grouping_page = TargetGroupingPage(page, BASE_URL)
    target_grouping_page.open_it()
    target_grouping_page.open_creation_page()

    expect(page).to_have_title(re.compile(r".*Login"))

def test_authorized_user_can_see_no_content_fallback(page: Page):

    target_grouping_page = TargetGroupingPage(page, BASE_URL)
    target_grouping_page.login(*VALID_USER_CREDENTIALS)
    target_grouping_table = target_grouping_page.get_target_groupings_table()

    expect(target_grouping_table).to_contain_text("No groups yet")

def test_authorized_user_can_create_target_groups(page: Page):

    target_grouping_page = TargetGroupingPage(page, BASE_URL)
    target_grouping_page.login(*VALID_USER_CREDENTIALS)
    target_grouping_page.create_group(TARGET_GROUP_NAME)
    target_grouping_table = target_grouping_page.get_target_groupings_table()

    expected_values= (
        ("Group", fr"{TARGET_GROUP_NAME}"),
        ("Total Targets", r"0"),
        ("Share", r"Share"),
        ("Delete", r"Delete"),
    )
    for i, info in enumerate(expected_values):
        key, value = info
        column_header = target_grouping_table.locator("thead th").nth(i)
        column_value = target_grouping_table.locator("tbody td").nth(i)
        expect(column_header).to_contain_text(re.compile(fr"{key}"))
        if value == "":
            expect(column_value).to_be_empty()
        else:
            expect(column_value).to_contain_text(re.compile(fr"{value}"))

def test_authorized_user_can_delete_target_groups(page: Page):

    target_grouping_page = TargetGroupingPage(page, BASE_URL)
    ANOTHER_GROUP = TARGET_GROUP_NAME + "2"
    target_grouping_page.login(*VALID_USER_CREDENTIALS)
    target_grouping_page.create_group(ANOTHER_GROUP)
    target_grouping_page.delete_group(ANOTHER_GROUP)
    target_grouping_table = target_grouping_page.get_target_groupings_table()

    expect(target_grouping_table).not_to_contain_text(fr"{ANOTHER_GROUP}")

def test_admin_user_can_assign_target_to_group(page: Page):

    target_grouping_page = TargetGroupingPage(page, BASE_URL)
    ANOTHER_GROUP = TARGET_GROUP_NAME + "3"
    target_grouping_page.login(*VALID_ADMIN_CREDENTIALS)
    target_grouping_page.create_group(ANOTHER_GROUP)

    targets_page = target_grouping_page.go_to_targets_page()
    target_name, target_ra, target_dec = "FOO", 1, 1
    targets_page.create_target(target_name, target_ra, target_dec)
    targets_page.open_it()
    targets_page.assign_target_to_group(ANOTHER_GROUP, target_name=target_name)

    SUCCESS_TEXT = f"1 target(s) successfully added to group '{ANOTHER_GROUP}'."
    banner = page.get_by_role("alert")
    expect(banner).to_contain_text(SUCCESS_TEXT)

def test_admin_user_can_move_target_to_group(page: Page):

    target_grouping_page = TargetGroupingPage(page, BASE_URL)
    ANOTHER_GROUP = TARGET_GROUP_NAME + "4"
    ANOTHER_GROUP_TARGET = TARGET_GROUP_NAME + "5"
    target_grouping_page.login(*VALID_ADMIN_CREDENTIALS)
    target_grouping_page.create_group(ANOTHER_GROUP)
    target_grouping_page.create_group(ANOTHER_GROUP_TARGET)

    targets_page = target_grouping_page.go_to_targets_page()
    target_name, target_ra, target_dec = "FOO", 1, 1
    targets_page.create_target(target_name, target_ra, target_dec)
    targets_page.open_it()
    targets_page.assign_target_to_group(ANOTHER_GROUP, target_name=target_name)

    SUCCESS_TEXT = f"1 target(s) successfully added to group '{ANOTHER_GROUP}'."
    banner = page.get_by_role("alert")
    expect(banner).to_contain_text(SUCCESS_TEXT)

    targets_page.move_target_to_group(ANOTHER_GROUP_TARGET, target_name=target_name)

    SUCCESS_TEXT_MOVE = f"1 target(s) successfully moved to group '{ANOTHER_GROUP_TARGET}'."
    banner = page.get_by_role("alert")
    expect(banner).to_contain_text(SUCCESS_TEXT_MOVE)

@pytest.mark.skip(reason="Due to a bug in tomtoolkit targets can not be removed from groups")
def test_authorized_user_can_remove_targets_from_target_groups(page: Page):
    pass

@pytest.mark.skip(reason="Due to a bug in tomtoolkit only admins can assign targets to groups")
def test_authorized_user_can_assign_target_groups(page: Page):
    pass




        
