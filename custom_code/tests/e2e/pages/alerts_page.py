import re
from playwright.sync_api import Page

class AlertsPage:
    def __init__(self, page: Page, base_url) -> None:
        self.page = page
        self.base_url = base_url

    def open_it(self):
        self.page.goto(f"{self.base_url}/alerts/query/list/")
    
    def login(self, username, password):
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("Password").fill(password)
        self.page.get_by_role("button", name="Login").click()

    def get_query_table(self):
        # This is very brittle. But I don't think I can easily add a testid here.
        return self.page.get_by_text(re.compile(r".*NameBrokerCreated.*")).locator('xpath=../..')
    
    def create_query(self, query_name, target_name):
        self.page.get_by_role("link", name="ALeRCE").click()
        #self.page.goto("http://localhost:8000/alerts/query/create/?broker=ALeRCE")
        self.page.get_by_role("textbox", name="Query name*").fill(query_name)
        self.page.get_by_role("textbox", name="Object ID").fill(target_name)
        self.page.get_by_role("button", name="Submit").click()

    def filter_query(self, broker_name, query_name):
        self.page.get_by_label("Broker").select_option(broker_name)
        self.page.get_by_role("textbox", name="Name contains").fill(query_name)
        self.page.get_by_role("button", name="Filter").click()