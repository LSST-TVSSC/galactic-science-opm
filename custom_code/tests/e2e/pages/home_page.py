import re
from playwright.sync_api import Page
from playwright.sync_api import expect

from custom_code.tests.e2e.pages.users_page import UsersPage

class HomePage:
    def __init__(self, page: Page, base_url) -> None:
        self.page = page
        self.base_url = base_url

    def open_it(self):
        self.page.goto(f"{self.base_url}/")

    def login(self, username, password):
        self.page.get_by_text("Login").click()
        expect(self.page).to_have_title(re.compile(r".*Login"))
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("Password").fill(password)
        self.page.get_by_role("button", name="Login").click()

    def register(self, username, first_name, last_name, email, password, password_confirm, affiliation):
        user_page = UsersPage(self.page, self.base_url)
        user_page.register(username, first_name, last_name, email, password, password_confirm, affiliation)

    def get_commit_hash_container(self):
        return self.page.get_by_test_id("commit-hash-container")
        
