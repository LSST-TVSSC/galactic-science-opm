import os
from playwright.sync_api import Page

class TargetsPage:
    def __init__(self, page: Page, base_url) -> None:
        self.page = page
        self.base_url = base_url

    def open_it(self):
        self.page.goto(f"{self.base_url}/targets/")

    def login(self, username, password):
        targets_table_container = self.page.get_by_test_id("targets-table")
        targets_table_container.get_by_role("link", name="login").click()
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("Password").fill(password)
        self.page.get_by_role("button", name="Login").click()
    
    def filter(self, search_term):
        self.page.get_by_role("textbox", name="Name", exact=True).fill(search_term)
        self.page.get_by_role("button", name="Filter", exact=True).click()
    
    def reset(self):
        self.page.get_by_role("link", name="Reset", exact=True).click()

    def get_filter_field(self, name):
        return self.page.get_by_role("textbox", name=name, exact=True)

    def create_target(self, /, name, ra, dec):
        self.page.get_by_role("button", name="Create Targets").click()
        self.page.get_by_role("link", name="Create a Target").click()
        self.page.get_by_role("textbox", name="Name").fill(str(name))
        self.page.get_by_role("textbox", name="Right Ascension*").fill(str(ra))
        self.page.get_by_role("textbox", name="Declination*").fill(str(dec))
        self.page.get_by_label("Known extragalactic*").select_option("not in GLADE+ galaxy catalog")
        self.page.get_by_role("button", name="Submit").click()

    def assign_target_to_group(self, group_name, target_name):
        self.page.locator("select[name=\"grouping\"]").select_option(label=group_name)
        self.page.get_by_role("row", name=f"{target_name} SIDEREAL 0").get_by_role("checkbox").check()
        self.page.get_by_role("button", name="Add").click()

    def move_target_to_group(self, group_name, target_name):
        self.page.locator("select[name=\"grouping\"]").select_option(label=group_name)
        self.page.get_by_role("row", name=f"{target_name} SIDEREAL 0").get_by_role("checkbox").check()
        self.page.get_by_role("button", name="Move", exact=True).click()

    def merge_targets(self, one, other):
        self.page.get_by_role("row", name=f"{one} SIDEREAL 0").get_by_role("checkbox").check()
        self.page.get_by_role("row", name=f"{other} SIDEREAL 0").get_by_role("checkbox").check()
        self.page.get_by_role("button", name="Merge").click()
        self.page.get_by_role("button", name="Confirm").click()

    def upload_targets(self, filepath):
        self.page.get_by_role("button", name="Create Targets").click()
        self.page.get_by_role("link", name="Import Targets").click()
        self.page.get_by_role("button", name="Choose File").set_input_files(filepath)
        self.page.get_by_role("button", name="Upload").click()
        self.page.get_by_text("Targets created:").click()

    def query_catalog(self, term, catalog):
        self.page.get_by_role("button", name="Create Targets").click()
        self.page.get_by_role("link", name="Catalog Search").click()
        self.page.get_by_role("textbox", name="Term").fill(term)
        self.page.get_by_label("Service").select_option(catalog)
        self.page.get_by_role("button", name="search").click()

    def update_broker_data(self):
        self.page.get_by_role("link", name="Update Broker Data").click()

    def export_data(self):
        BASE_PATH = os.path.dirname(os.path.abspath(__file__))
        with self.page.expect_download() as download:
            self.page.get_by_role("button", name="Export Filtered Targets").click()
        
        path_to_download = os.path.join(BASE_PATH, download.value.suggested_filename)
        # Wait for the download process to complete and save the downloaded file somewhere
        download.value.save_as(path_to_download)
        return path_to_download
