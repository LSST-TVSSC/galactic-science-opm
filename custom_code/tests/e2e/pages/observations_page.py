from playwright.sync_api import Page

class ObservationsPage:
    def __init__(self, page: Page, base_url) -> None:
        self.page = page
        self.base_url = base_url

    def open_it(self):
        self.page.goto(f"{self.base_url}/observations/status/")

    def get_map(self):
        return self.page.locator(".plot-container svg.main-svg").first


    def get_facility_status_table(self):
        """
        The facilities are loaded asynchronously and this can take a couple of seconds.
        """
        placeholder = self.page.get_by_role("cell", name="Fetching facility status...")
        placeholder.wait_for(state="hidden", timeout=20_000)
        return self.page.locator("#facility-status-list table")