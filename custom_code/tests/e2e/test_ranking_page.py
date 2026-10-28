import re
from datetime import datetime
from zoneinfo import ZoneInfo

from playwright.sync_api import Page, expect

from custom_code.tests.e2e.data.test_data import BASE_URL, BROKER_LINKS
from custom_code.tests.e2e.pages.ranking_page import RankingPage

NUMBER_OF_ELEMENTS_WITH_CORRECT_PROBABILITY = 11


def test_should_render_all_tables_correctly(page: Page):
    pks_per_row = (45, 46, 47)
    creation_date = "2026-04-30, 6:53 AM"
    today = datetime.now(ZoneInfo("UTC"))
    as_date = datetime.strptime(creation_date, "%Y-%m-%d, %I:%M %p").replace(
        tzinfo=ZoneInfo("UTC")
    )

    ranking_page = RankingPage(page, BASE_URL)
    ranking_page.open_it()

    def days_ago(d):
        return (today - d).days

    created_ago = days_ago(as_date)

    baade_map_container = page.get_by_test_id("baade-map")
    problist_title = page.get_by_test_id("problist-title")
    expect(baade_map_container.locator("img")).to_be_visible()
    expect(problist_title).to_contain_text(
        re.compile(
            "Public ranking based on averaged and rescaled probabilities of a quantile transform"
        )
    )

    # first table
    expected_rows = (
        (
            r"OGLE-2026-OPM-0001\s+ALeRCE\s+fink\s+ANTARES",  # name
            "",
            r"NA",
            r"1(\s+|.+|)1",
            1.0,  # prob rescaled average
            "None",  # variability flags
            created_ago,  # days since created
            0.000,  # gaia nsup2
            0.000,  # bhrf rescaled
            0.000,  # bhrf contrast
            0.000,  # atat direct
            0.000,  # microlensing filter
            0.000,  # psi rescaled
            0.000,  # bogus
            "April 30, 2026, 6:53 a.m.",  # updated
        ),
        (
            r"OGLE-2026-OPM-0002\s+ALeRCE\s+fink\s+ANTARES",
            "",
            r"NA",
            r"1(\s+|.+|)1",
            1.0,  # prob rescaled average
            "None",  # variability flags
            created_ago,  # days since created
            0.000,  # gaia nsup2
            0.000,  # bhrf rescaled
            0.000,  # bhrf contrast
            0.000,  # atat direct
            0.000,  # microlensing filter
            0.000,  # psi rescaled
            0.000,  # bogus
            "April 30, 2026, 6:53 a.m.",
        ),
        (
            r"OGLE-2026-OPM-0003\s+ALeRCE\s+fink\s+ANTARES",
            "",
            r"NA",
            r"1(\s+|.+|)1",
            1.0,  # prob rescaled average
            "None",  # variability flags
            created_ago,  # days since created
            0.000,  # gaia nsup2
            0.000,  # bhrf rescaled
            0.000,  # bhrf contrast
            0.000,  # atat direct
            0.000,  # microlensing filter
            0.000,  # psi rescaled
            0.000,  # bogus
            "April 30, 2026, 6:53 a.m.",
        ),
    )

    ranking_table_survey_known_variability = page.get_by_test_id(
        "ranking_table_survey_teams"
    )
    ranking_table_known_var_headline = page.get_by_test_id(
        "ranking_table_survey_teams__headline"
    )
    expect(ranking_table_survey_known_variability).to_be_visible()
    expect(ranking_table_known_var_headline).to_contain_text(
        "ZTF or LSST Microlensing candidates also discovered by survey teams"
    )

    results_rows = ranking_table_survey_known_variability.locator("tbody tr")
    ztf_alias_names = ("ZTF26fakeala", "ZTF26fakealb", "ZTF26fakealc")

    for i, row in enumerate(expected_rows):
        alias = ztf_alias_names[i]
        table_row = results_rows.nth(i)
        for j, field in enumerate(row):
            pk = pks_per_row[i]
            cell = table_row.locator("td").nth(j)
            if field != "":
                expect(cell).to_contain_text(re.compile(rf"{field}"))
            else:
                expect(cell).to_be_empty()
            if j == 0:
                target_name, _, _, _ = field.split(r"\s+")
                target_link = cell.get_by_role("link", name=target_name)
                expect(target_link).to_have_attribute("href", f"/targets/{pk}/")
                for link in BROKER_LINKS:
                    target_link = cell.get_by_role("link", name=link["name"])
                    expect(target_link).to_have_attribute(
                        "href", link["href"].format(alias)
                    )

    # second table
    expected_rows = (
        (
            r"ZTF26aarbgfh\s+ALeRCE\s+fink\s+ANTARES",  # name
            "",
            r"16.07\s+\(ZTF_r\)",
            r"274.57781(\s+|.+|)2.05696",
            0.4639,  # prob rescaled average
            "None, queried",  # variability flags
            created_ago,  # days since created
            0.923,  # gaia nsup2
            0.932,  # bhrf rescaled
            0.000,  # bhrf contrast
            0.000,  # atat direct
            0.000,  # microlensing filter
            0.000,  # psi rescaled
            0.085,  # bogus
            "April 30, 2026, 6:53 a.m.",  # updated
        ),
        (
            r"ZTF26aaivmks\s+ALeRCE\s+fink\s+ANTARES",
            "active",
            r"16.56\s+\(ZTF_i\)",
            r"283.17555(\s+|.+|)0.46239",
            0.4616,
            "None, queried",
            created_ago,
            0.920,
            0.926,
            0.000,
            0.000,
            0.000,
            0.000,
            0.166,
            "April 30, 2026, 6:53 a.m.",
        ),
        (
            r"LSST_133721466018857001\s+ALeRCE\s+ANTARES",
            "",
            r"NA",
            r"1(\s+|.+|)1",
            0.4600,  # prob rescaled average
            "None, queried",  # variability flags
            created_ago,  # days since created
            0.000,  # gaia nsup2
            0.000,  # bhrf rescaled
            0.000,  # bhrf contrast
            0.000,  # atat direct
            0.000,  # microlensing filter
            0.000,  # psi rescaled
            0.000,  # bogus
            "April 30, 2026, 6:53 a.m.",
        ),
    )

    ranking_table_survey_known_variability = page.get_by_test_id(
        "ranking_table_no_variablilty"
    )
    ranking_table_known_var_headline = page.get_by_test_id(
        "ranking_table_no_variablilty__headline"
    )
    expect(ranking_table_survey_known_variability).to_be_visible()
    expect(ranking_table_known_var_headline).to_contain_text(
        "Ranked ZTF or LSST Microlensing candidates without known variability"
    )

    results_rows = ranking_table_survey_known_variability.locator("tbody tr")
    pks_per_row = (3, 4, 48)
    for i, row in enumerate(expected_rows):
        table_row = results_rows.nth(i)
        for j, field in enumerate(row):
            pk = pks_per_row[i]
            cell = table_row.locator("td").nth(j)
            if field != "":
                expect(cell).to_contain_text(re.compile(rf"{field}"))
            else:
                expect(cell).to_be_empty()
            if j == 0:
                is_lsst = False
                if "LSST" in str(field):
                    target_name, _, _ = field.split(r"\s+")
                    is_lsst = True
                else:
                    target_name, _, _, _ = field.split(r"\s+")

                target_link = cell.get_by_role("link", name=target_name)
                expect(target_link).to_have_attribute("href", f"/targets/{pk}/")
                for link in BROKER_LINKS:
                    # There is no fink link for lsst targets
                    if is_lsst and link["name"] == "Fink":
                        continue
                    target_link = cell.get_by_role("link", name=link["name"])
                    expect(target_link).to_have_attribute(
                        "href", link["href"].format(target_name)
                    )

    # third table
    expected_rows = (
        (
            r"ZTF26aaggluu\s+ALeRCE\s+fink\s+ANTARES",  # name
            "",
            r"20.32\s+\(ZTF_r\)",
            r"187.58942(\s+|.+|)14.15461",
            0.0328,  # prob rescaled average
            "None",  # variability flags
            created_ago,  # days since created
            0.131,  # gaia nsup2
            0.000,  # bhrf rescaled
            0.000,  # bhrf contrast
            0.000,  # atat direct
            0.000,  # microlensing filter
            0.000,  # psi rescaled
            0.102,  # bogus
            "April 30, 2026, 6:53 a.m.",  # updated
        ),
        (
            r"ZTF26aalcpif\s+ALeRCE\s+fink\s+ANTARES",
            "bogus",
            r"19.13\s+\(ZTF_r\)",
            r"171.58098(\s+|.+|)8.78074",
            0.0143,
            "None",
            created_ago,
            0.057,
            0.000,
            0.000,
            0.000,
            0.000,
            0.000,
            0.690,
            "April 30, 2026, 6:53 a.m.",
        ),
    )

    ranking_table_survey_known_variability = page.get_by_test_id(
        "ranking_table_known_variability"
    )
    ranking_table_known_var_headline = page.get_by_test_id(
        "ranking_table_known_variablilty__headline"
    )
    expect(ranking_table_survey_known_variability).to_be_visible()
    expect(ranking_table_known_var_headline).to_contain_text(
        "Ranked ZTF or LSST Microlensing candidates with known variability or failing catalog queries"
    )

    results_rows = ranking_table_survey_known_variability.locator("tbody tr")
    pks_per_row = (36, 23)
    for i, row in enumerate(expected_rows):
        table_row = results_rows.nth(i)
        for j, field in enumerate(row):
            pk = pks_per_row[i]
            cell = table_row.locator("td").nth(j)
            if field != "":
                expect(cell).to_contain_text(re.compile(rf"{field}"))
            else:
                expect(cell).to_be_empty()
            if j == 0:
                is_lsst = False
                if "LSST" in str(field):
                    target_name, _, _ = field.split(r"\s+")
                    is_lsst = True
                else:
                    target_name, _, _, _ = field.split(r"\s+")

                target_link = cell.get_by_role("link", name=target_name)
                expect(target_link).to_have_attribute("href", f"/targets/{pk}/")
                for link in BROKER_LINKS:
                    # There is no fink link for lsst targets
                    if is_lsst and link["name"] == "Fink":
                        continue
                    target_link = cell.get_by_role("link", name=link["name"])
                    expect(target_link).to_have_attribute(
                        "href", link["href"].format(target_name)
                    )


def all_targets_are_displayed(page: Page):
    pks_per_row = (3, 4, 6)
    creation_date = "2026-04-30, 6:53 AM"
    today = datetime.now(ZoneInfo("UTC"))
    as_date = datetime.strptime(creation_date, "%Y-%m-%d, %I:%M %p").replace(
        tzinfo=ZoneInfo("UTC")
    )

    def days_ago(d):
        return (today - d).days

    created_ago = days_ago(as_date)
    expected_rows = (
        (
            r"ZTF26aarbgfh\s+ALeRCE\s+fink\s+ANTARES",  # name
            "",
            r"16.07\s+\(ZTF_r\)",
            r"274.57781(\s+|.+|)2.05696",
            0.4639,  # prob rescaled average
            "None, queried",  # variability flags
            created_ago,  # days since created
            0.923,  # gaia nsup2
            0.932,  # bhrf rescaled
            0.000,  # bhrf contrast
            0.000,  # atat direct
            0.000,  # microlensing filter
            0.000,  # psi rescaled
            0.085,  # bogus
            "April 30, 2026, 6:53 a.m.",  # updated
        ),
        (
            r"ZTF26aaivmks\s+ALeRCE\s+fink\s+ANTARES",
            "active",
            r"16.56\s+\(ZTF_i\)",
            r"283.17555(\s+|.+|)0.46239",
            0.4616,
            "None, queried",
            created_ago,
            0.920,
            0.926,
            0.000,
            0.000,
            0.000,
            0.000,
            0.166,
            "April 30, 2026, 6:53 a.m.",
        ),
        (
            r"ZTF26aajaofr\s+ALeRCE\s+fink\s+ANTARES",
            "",
            r"16.58\s+\(ZTF_i\)",
            r"274.50616(\s+|.+|)\-3.99875",
            0.4580,
            "None, queried",
            created_ago,
            0.925,
            0.907,
            0.000,
            0.000,
            0.000,
            0.000,
            0.139,
            "April 30, 2026, 6:53 a.m.",
        ),
    )
    ranking_page = RankingPage(page, BASE_URL)
    ranking_page.open_it()

    baade_map_container = page.get_by_test_id("baade-map")
    problist_title = page.get_by_test_id("problist-title")
    expect(baade_map_container.locator("img")).to_be_visible()
    expect(problist_title).to_contain_text(
        re.compile(
            "Public ranking based on averaged and rescaled probabilities of a quantile transform"
        )
    )

    ranking_table = page.get_by_test_id("ranking_table")
    expect(ranking_table).to_be_visible()

    results_rows = ranking_table.locator("tbody tr")
    expect(results_rows).to_have_count(NUMBER_OF_ELEMENTS_WITH_CORRECT_PROBABILITY)

    for i, row in enumerate(expected_rows):
        table_row = results_rows.nth(i)
        for j, field in enumerate(row):
            pk = pks_per_row[i]
            cell = table_row.locator("td").nth(j)
            if field != "":
                expect(cell).to_contain_text(re.compile(rf"{field}"))
            else:
                expect(cell).to_be_empty()
            if j == 0:
                target_name, _, _, _ = field.split(r"\s+")
                target_link = cell.get_by_role("link", name=target_name)
                expect(target_link).to_have_attribute("href", f"/targets/{pk}/")
                for link in BROKER_LINKS:
                    target_link = cell.get_by_role("link", name=link["name"])
                    expect(target_link).to_have_attribute(
                        "href", link["href"].format(target_name)
                    )
