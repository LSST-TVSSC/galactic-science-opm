from playwright.sync_api import Page
from playwright.sync_api import expect
import os
class TargetPage:
    def __init__(self, page: Page, base_url, target_pk) -> None:
        self.page = page
        self.base_url = base_url
        self.target_pk = target_pk

    def open_it(self):
        self.page.goto(f"{self.base_url}/targets/{self.target_pk}")

    def login(self, username, password):
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("Password").fill(password)
        self.page.get_by_role("button", name="Login").click()

    def export_data(self):
        BASE_PATH = os.path.dirname(os.path.abspath(__file__))
        with self.page.expect_download() as download:
            self.page.get_by_role("button", name="Download lightcurve data for target").click()
        
        path_to_download = os.path.join(BASE_PATH, download.value.suggested_filename)
        # Wait for the download process to complete and save the downloaded file somewhere
        download.value.save_as(path_to_download)
        return path_to_download

