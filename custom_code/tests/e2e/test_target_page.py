import os
import re
from playwright.sync_api import Page, expect
from custom_code.tests.e2e.data.test_data import BASE_URL, TOP_TARGETS, VALID_USER_CREDENTIALS
from custom_code.tests.e2e.pages.target_page import TargetPage

TEST_TARGET = TOP_TARGETS[0]

def test_unauthorized_user_can_not_visit(page: Page):
    target_page = TargetPage(page, BASE_URL, TEST_TARGET["pk"])
    target_page.open_it()
    hint_text = (
        "You do not have permission to access this page. "
        "Please login as a user with the correct permissions or contact your PI."
    )
    expect(page).to_have_title(re.compile(r".*Login"))
    
    hint = page.get_by_text(hint_text)
    expect(hint).to_be_visible()
    expect(hint).to_have_attribute("class", re.compile(r".*alert"))

def test_authorized_user_can_visit(page: Page):

    PORTALS_VARIANT_1 = (
        ("ALeRCE", "https://alerce.online/object/{name}"),
        ("fink", "https://ztf.fink-portal.org/{name}"),
        ("Vizier Gaia DR3", "https://vizier.cds.unistra.fr/cgi-bin/VizieR?-source=gaia-dr3&-c={ra},{dec}&-c.rs=1"),
        ("SED Vizier", "https://vizier.cds.unistra.fr/vizier/sed/?-c={ra},{dec}&-c.rs=2")
    )
    PORTALS_VARIANT_2 = (
        ("ALeRCE", "https://alerce.online/object/{name}"),
        ("fink", "https://ztf.fink-portal.org/{name}"),
        ("Vizier Gaia DR3", "https://vizier.cds.unistra.fr/cgi-bin/VizieR?-source=gaia-dr3&-c={ra},{dec}&-c.rs=2"),
        ("SED Vizier", "https://vizier.cds.unistra.fr/vizier/sed/?-c={ra},{dec}&-c.rs=2")
    )
    EXPECTED_TARGET_INFO = (
        ('Names', "ZTF26aarbgfh"),
        ('RA', '18:18:18.673'),
        ('Dec', '00:08:13.669'),
        ('Class', 'Microlensing candidate'),
        ('Probability rescaled', '0.464'),
    )
    EXPECTED_PARAMETERS = (
        (r"t0\s\[JD\]", 11053.599),
        ("u0", 0.000),
        (r"tE\s\[days\]", 64.774),
        ("ρ", 1.163),
        ("πEE", 0.000),
        ("πEN", 0.000),
    )
    EXPECTED_CLASSIFICATION_VALUES = (
        ("Averaged Rescaled Probability", 0.464),
        ("Gaia normalized N² Rescaled", 0.923),
        ("ALeRCE microlensing BHRF Rescaled", 0.932),
        ("fink microlensing peak Rescaled", 0.000),
        ("Peak Planet Probability from fit ψ Rescaled", 0.000),
        ("Bogus ALeRCE stamp", 0.085),
        ("Updated rescaled probabilities", "2026-04-30 06:53:51"),
    )
    EXPECTED_ANALYSIS_PARAMETERS = (
        (r"t0\s\[HJD\]", r"11053.599∓\s+12.206"),
        ("u0", r"0.0000∓\s+1718.0719"),
        (r"tE\s\[days\]", r"64.774∓\s+46.535"),
        (r"πEE", r"0.000∓\s+0.000"),
        ("πEN", r"0.000∓\s+0.000"),
        ("ρ", r"1.163∓\s+0.929"),
        ("s", r"0.000∓\s+0.000"),
        ("q", r"0.000∓\s+"),
        ("α", r"0.000∓\s+0.000"),
    )
    EXPECTED_MAGNITUDE_VALUES= (
        (r"Source magnitude", r"∓"),
        ("Blend magnitude", r"∓"),
        (r"Baseline magnitude", r"∓"),
        (r"Current magnitude", ""),
    )

    target_page = TargetPage(page, BASE_URL, TEST_TARGET["pk"])
    target_page.open_it()
    target_page.login(*VALID_USER_CREDENTIALS)

    expect(page).to_have_title(re.compile(r".*Target ZTF26aarbgfh"))

    target_info_container = page.get_by_test_id("target-info")
    for key, value in EXPECTED_TARGET_INFO:
        expect(target_info_container).to_contain_text(re.compile(fr".*{key}\s+{value}"))

    parameter_table = page.get_by_test_id("parameter-table")
    for i, info in enumerate(EXPECTED_PARAMETERS):
        key, value = info
        column_header = parameter_table.locator("thead th").nth(i)
        column_value = parameter_table.locator("tbody td").nth(i)
        expect(column_header).to_contain_text(re.compile(fr"{key}"))
        expect(column_value).to_contain_text(re.compile(fr"{value}"))

    # go through tabs
    ## Imaging
    page.get_by_role("tab", name="Imaging").click()
    imaging_tab = page.get_by_test_id("imaging-tab")
    expect(imaging_tab).to_be_visible()
    expect(imaging_tab).to_contain_text("Survey View")
    # mkistner: i am not sure about this test. It is very closely tied to 
    # an external package
    aladin_container = imaging_tab.get_by_test_id("aladin-container")
    expect(aladin_container).not_to_be_empty()
    # mkistner: @todo: check if inputs to aladin chart are needed for tests

    ## Photometry
    page.get_by_role("tab", name="Photometry").click()
    photometry_tab = page.get_by_test_id("photometry-tab")
    expect(photometry_tab).to_be_visible()
    # mkistner: also not sure about this assertion...
    light_curve_chart_container = photometry_tab.locator(".light-curve")
    expect(light_curve_chart_container).to_be_visible()
    expect(light_curve_chart_container).not_to_be_empty()
    
    for name, href in PORTALS_VARIANT_1:
        target_name = TEST_TARGET["name"]
        ra, dec = TEST_TARGET["coordinates"]
        link = photometry_tab.get_by_role("button", name=name)
        expect(link).to_have_attribute("href", href.format(name=target_name, ra=ra, dec=dec))

    ## Spectroscopy (seems a bit WIP right now)
    page.get_by_role("tab", name="Spectroscopy").click()
    spectroscopy_tab = page.get_by_test_id("spectroscopy-tab")
    expect(spectroscopy_tab).to_be_visible()

    for name, href in PORTALS_VARIANT_2:
        target_name = TEST_TARGET["name"]
        ra, dec = TEST_TARGET["coordinates"]
        link = spectroscopy_tab.get_by_role("button", name=name)
        expect(link).to_have_attribute("href", href.format(name=target_name, ra=ra, dec=dec))

    ## Classifications
    page.get_by_role("tab", name="Classifications").click()
    classifications_tab = page.get_by_test_id("classifications-tab")
    expect(classifications_tab).to_be_visible()
    ### chart
    # mkistner: I am not sure about this test; coupled to implementation detail
    chart_container = classifications_tab.locator(".plotly-graph-div")
    expect(chart_container).to_be_visible()
    expect(chart_container).not_to_be_empty()

    ### table
    classifications_table = classifications_tab.get_by_test_id("classification-table")
    
    for i, info in enumerate(EXPECTED_CLASSIFICATION_VALUES):
        key, value = info
        column_header = classifications_table.locator("thead th").nth(i)
        column_value = classifications_table.locator("tbody td").nth(i)
        expect(column_header).to_contain_text(re.compile(fr"{key}"))
        expect(column_value).to_contain_text(re.compile(fr"{value}"))

    for name, href in PORTALS_VARIANT_1:
        target_name = TEST_TARGET["name"]
        ra, dec = TEST_TARGET["coordinates"]
        link = classifications_tab.get_by_role("button", name=name)
        expect(link).to_have_attribute("href", href.format(name=target_name, ra=ra, dec=dec))

    ## Analysis
    page.get_by_role("tab", name="Analysis").click()
    analysis_tab = page.get_by_test_id("analysis-tab")
    expect(analysis_tab).to_be_visible()

    ### table for parameters
    analysis_table = analysis_tab.get_by_test_id("analysis-table_parameters")
    for i, info in enumerate(EXPECTED_ANALYSIS_PARAMETERS):
        key, value = info
        column_header = analysis_table.locator("thead th").nth(i)
        column_value = analysis_table.locator("tbody td").nth(i)
        expect(column_header).to_contain_text(re.compile(fr"{key}"))
        expect(column_value).to_contain_text(re.compile(fr"{value}"))
    
    ### table for magnitude
    analysis_table_magnitude = analysis_tab.get_by_test_id("analysis-table_magnitude")
    for i, info in enumerate(EXPECTED_MAGNITUDE_VALUES):
        key, value = info
        column_header = analysis_table_magnitude.locator("thead th").nth(i)
        column_value = analysis_table_magnitude.locator("tbody td").nth(i)
        expect(column_header).to_contain_text(re.compile(fr"{key}"))
        if value == "":
            expect(column_value).to_be_empty()
        else:
            expect(column_value).to_contain_text(re.compile(fr"{value}"))

    ## Exchange
    page.get_by_role("tab", name="Exchange").click()
    exchange_tab = page.get_by_test_id("exchange-tab")
    expect(exchange_tab).to_be_visible()










