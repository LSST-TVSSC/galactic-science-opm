import re
from playwright.sync_api import Page
from playwright.sync_api import expect

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
        self.page.get_by_text("Register").click()
        expect(self.page).to_have_title(re.compile(r".*Sign up"))
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("First name").fill(first_name)
        self.page.get_by_placeholder("Last name").fill(last_name)
        self.page.get_by_placeholder("Email").fill(email)
        self.page.get_by_placeholder("Password", exact=True).fill(password)
        self.page.get_by_placeholder("Password confirmation").fill(password_confirm)
        self.page.get_by_placeholder("Affiliation").fill(affiliation)
        self.page.get_by_role("button", name="Register").click()

