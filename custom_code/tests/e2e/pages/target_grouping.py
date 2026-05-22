from playwright.sync_api import Page

from custom_code.tests.e2e.pages.targets_page import TargetsPage

class TargetGroupingPage:
    def __init__(self, page: Page, base_url) -> None:
        self.page = page
        self.base_url = base_url

    def open_it(self):
        self.page.goto(f"{self.base_url}/targets/targetgrouping/")

    def go_to_targets_page(self):
        targets_page = TargetsPage(self.page, self.base_url)
        targets_page.open_it()
        return targets_page

    def login(self, username, password):
        self.page.goto(f"{self.base_url}/targets/targetgrouping/")
        self.page.get_by_role("link", name="Login").click()
        self.page.get_by_role("textbox", name="Username").fill(username)
        self.page.get_by_role("textbox", name="Password").fill(password)
        self.page.get_by_role("button", name="Login").click()
        self.page.goto(f"{self.base_url}/targets/targetgrouping/")

    def open_creation_page(self):
        self.page.get_by_role("link", name="Create New Grouping").click()

    def create_group(self, name):
        self.open_creation_page()
        self.page.get_by_role("textbox", name="Name:").fill(name)
        self.page.get_by_role("button", name="Create").click()

    def get_target_groupings_table(self):
        return self.page.get_by_test_id("target-groupings-table")

    def delete_group(self, name):
        self.page.get_by_role("link", name="Delete").first.click()
        self.page.get_by_role("button", name="Confirm").click()