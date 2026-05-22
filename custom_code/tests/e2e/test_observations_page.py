from playwright.sync_api import Page, expect

from custom_code.tests.e2e.data.test_data import BASE_URL
from custom_code.tests.e2e.pages.observations_page import ObservationsPage

"""
Since this is a module provided by tomtoolkit, the testing done here
should be minimal.
"""

def test_observations_page_is_available(page: Page):
    MINIMUM_EXPECTED_AMOUNT_OF_FACILITIES = 5

    observations_page = ObservationsPage(page, BASE_URL)
    observations_page.open_it()

    observations_table = observations_page.get_facility_status_table()
    world_map = observations_page.get_map()
    location_rows = observations_table.locator("tbody tr")

    assert (location_rows.count()) > MINIMUM_EXPECTED_AMOUNT_OF_FACILITIES
    expect(world_map).to_be_visible()