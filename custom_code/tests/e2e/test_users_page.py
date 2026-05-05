import re
from playwright.sync_api import Page, expect
from custom_code.tests.e2e.data.test_data import BASE_URL, VALID_USER_CREDENTIALS, VALID_ADMIN_CREDENTIALS

from custom_code.tests.e2e.pages.users_page import UsersPage

USER_DATA = ("max", "m k", "mk@example.com")
NEW_USER = ("new-man", "new", "new", "new@example.com", "1234!!!!", "1234!!!!", "affiliation")

def test_unauthorized_user_can_not_view_page(page: Page):

    users_page = UsersPage(page, BASE_URL)
    users_page.open_it()
    
    expect(page).to_have_title(re.compile(r".*Login"))

# This is a feature by tomtoolkit and we don't override the templates,
# so tests for this should be minimal, I think
def test_authorized_user_can_see_own_profile(page: Page):

    USER_NAME = VALID_USER_CREDENTIALS[0]

    users_page = UsersPage(page, BASE_URL)
    users_page.open_it()
    users_page.login(*VALID_USER_CREDENTIALS)

    users_page.open_profile(USER_NAME)

    profile_content = page.locator(".container .card")
    expect(profile_content).to_contain_text(re.compile(fr".*{USER_NAME}"))

def test_authorized_user_can_see_own_data_in_active_users(page: Page):

    users_page = UsersPage(page, BASE_URL)
    users_page.open_it()
    users_page.login(*VALID_USER_CREDENTIALS)

    for data in USER_DATA:
        cell = page.get_by_role("cell", name=data)
        expect(cell).to_be_visible()

def test_authorized_user_logout(page: Page):

    users_page = UsersPage(page, BASE_URL)
    users_page.open_it()
    users_page.login(*VALID_USER_CREDENTIALS)

    expect(page).to_have_title(re.compile(r".*User Management"))
    users_page.user_is_logged_in()

    users_page.logout()
    users_page.user_is_logged_out()


def test_admin_can_delete_pending_users(page: Page):

    users_page = UsersPage(page, BASE_URL)
    users_page.open_it()
    users_page.register(*NEW_USER)

    users_page.open_it()
    users_page.login(*VALID_ADMIN_CREDENTIALS)
    users_page.open_it()
    previous_number_pending_users = users_page.get_number_of_pending_users()
    assert previous_number_pending_users > 0

    users_page.delete_pending_user(NEW_USER[0])

    assert users_page.get_number_of_pending_users() == previous_number_pending_users -1

def test_admin_can_approve_pending_users(page: Page):

    users_page = UsersPage(page, BASE_URL)
    users_page.open_it()
    users_page.register(*NEW_USER)

    users_page.open_it()
    users_page.login(*VALID_ADMIN_CREDENTIALS)
    users_page.open_it()
    previous_number_pending_users = users_page.get_number_of_pending_users()
    assert previous_number_pending_users > 0

    users_page.approve(NEW_USER[0])

    assert users_page.get_number_of_pending_users() == previous_number_pending_users - 1

# This is a feature by tomtoolkit and we don't override the templates,
# so tests for this should be minimal, I think
def test_admin_can_see_groups(page: Page):

    users_page = UsersPage(page, BASE_URL)
    users_page.open_it()
    users_page.login(*VALID_ADMIN_CREDENTIALS)
    users_page.open_it()

    assert users_page.get_number_of_groups() == 1

# This is a feature by tomtoolkit and we don't override the templates,
# so tests for this should be minimal, I think
def test_admin_can_active_users(page: Page):

    users_page = UsersPage(page, BASE_URL)
    users_page.open_it()
    users_page.login(*VALID_ADMIN_CREDENTIALS)
    users_page.open_it()

    assert users_page.get_number_of_active_users() > 1

    
        