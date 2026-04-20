import os
import re
from playwright.sync_api import expect
from custom_code.tests.e2e.pages.home_page import HomePage

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

def test_created_user_can_login(page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.login("max", "tests")
    expect(page).to_have_title(re.compile(r".*Home"))

def test_unknown_user_can_not_login(page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.login("foo", "bad")
    expect(page).to_have_title(re.compile(r".*Login"))
    hint_text = "Please enter a correct username and password. Note that both fields may be case-sensitive."
    expect(page.get_by_role("alert")).to_contain_text(hint_text)

# also test 
# missing fields
def test_user_can_register(page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.register("dude3", "dude", "duderson", "dude@example.com", "foo1234%", "foo1234%", "dev") # one with less than 8
    expect(page).to_have_title(re.compile(r".*Home"))
    hint_text = "Your request to register has been submitted to the administrators."
    expect(page.get_by_role("alert")).to_contain_text(hint_text)

def test_existing_user_can_not_register(page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.register("max", "dude", "duderson", "dude@example.com", "foo1234%", "foo1234%", "dev")
    expect(page).to_have_title(re.compile(r".*Sign up"))
    hint_text = "A user with that username already exists."
    expect(page.get_by_text(hint_text)).to_be_visible()

def test_user_with_too_short_password_can_not_register(page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.register("bar", "dude", "duderson", "dude@example.com", "foo", "foo", "dev")
    expect(page).to_have_title(re.compile(r".*Sign up"))
    hint_text = "This password is too short. It must contain at least 8 characters."
    expect(page.get_by_text(hint_text)).to_be_visible()

# parameterize?
def test_user_with_invalid_user_name_can_not_register_dollar(page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.register("$", "dude", "duderson", "dude@example.com", "foo", "foo", "dev")
    expect(page).to_have_title(re.compile(r".*Sign up"))
    hint_text = "Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters."
    expect(page.get_by_text(hint_text)).to_be_visible()



