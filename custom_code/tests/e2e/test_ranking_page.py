import re
from playwright.sync_api import Page, expect
from custom_code.tests.e2e.data.test_data import BASE_URL, BROKER_LINKS
from custom_code.tests.e2e.pages.ranking_page import RankingPage

NUMBER_OF_ELEMENTS_WITH_CORRECT_PROBABILITY = 11

def test_all_targets_are_displayed(page: Page):
    pks_per_row = (3,4,6)
    expected_rows = (
        (
            r"ZTF26aarbgfh\s+ALeRCE\s+fink\s+ANTARES",
            0.464,
            0.923,
            0.932,
            "NA",
            0.000,
            0.000,
            0.085,
            "2026-04-30 06:53:51",
        ),
        (
            r"ZTF26aaivmks\s+ALeRCE\s+fink\s+ANTARES",
            0.462,
            0.920,
            0.926,
            "NA",
            0.000,
            0.000,
            0.166,
            "2026-04-30 06:53:51",
        ),
        (
            r"ZTF26aajaofr\s+ALeRCE\s+fink\s+ANTARES",
            0.458,
            0.925,
            0.907,
            "NA",
            0.000,
            0.000,
            0.139,
            "2026-04-30 06:53:51",
        ),
    )
    ranking_page = RankingPage(page, BASE_URL)
    ranking_page.open_it()

    baade_map_container = page.get_by_test_id("baade-map")
    expect(baade_map_container.locator("img")).to_be_visible()
    expect(baade_map_container).to_contain_text(re.compile(
        "Public ranking based on averaged and rescaled probabilities of a quantile transform."
    ))

    ranking_table = page.get_by_test_id("ranking_table")
    expect(ranking_table).to_be_visible()

    results_rows = ranking_table.locator("tbody tr")
    expect(results_rows).to_have_count(
        NUMBER_OF_ELEMENTS_WITH_CORRECT_PROBABILITY
    )

    for i, row in enumerate(expected_rows):
        table_row = results_rows.nth(i)
        for j, field in enumerate(row):
            pk = pks_per_row[i]    
            cell = table_row.locator("td").nth(j)
            expect(cell).to_contain_text(re.compile(fr"{field}"))
            if j == 0:
                target_name, _, _, _ = field.split(r"\s+")
                target_link = cell.get_by_role("link", name=target_name)
                expect(target_link).to_have_attribute("href", f"/targets/{pk}/")
                for link in BROKER_LINKS:
                    target_link = cell.get_by_role("link", name=link["name"])
                    expect(target_link).to_have_attribute(
                        "href", link["href"].format(target_name)
                    )

    