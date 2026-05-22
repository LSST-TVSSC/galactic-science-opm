from playwright.sync_api import Page
from playwright.sync_api import expect

class RankingPage:
    def __init__(self, page: Page, base_url) -> None:
        self.page = page
        self.base_url = base_url

    def open_it(self):
        self.page.goto(f"{self.base_url}/custom_code/prob_list.html")

    def login(self, username, password):
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("Password").fill(password)
        self.page.get_by_role("button", name="Login").click()