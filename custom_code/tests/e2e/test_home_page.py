import os
import re
from playwright.sync_api import Page, expect
from custom_code.tests.e2e.data.test_data import BASE_URL, BROKER_LINKS, REGISTERABLE_USER, TOP_TARGETS, VALID_USER_CREDENTIALS
from custom_code.tests.e2e.pages.home_page import HomePage

def test_created_user_can_login(page: Page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.login(*VALID_USER_CREDENTIALS)
    expect(page).to_have_title(re.compile(r".*Home"))


def test_unknown_user_can_not_login(page: Page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.login("foo", "bad")
    expect(page).to_have_title(re.compile(r".*Login"))
    hint_text = "Please enter a correct username and password. Note that both fields may be case-sensitive."
    expect(page.get_by_role("alert")).to_contain_text(hint_text)



def test_user_can_register(page: Page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.register(**REGISTERABLE_USER)
    expect(page).to_have_title(re.compile(r".*Home"))
    hint_text = "Your request to register has been submitted to the administrators."
    expect(page.get_by_role("alert")).to_contain_text(hint_text)


def test_existing_user_can_not_register(page: Page):
    USERNAME_OF_SEEDED_USER = VALID_USER_CREDENTIALS[0]
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.register(**{**REGISTERABLE_USER, **{"username": USERNAME_OF_SEEDED_USER}})

    expect(page).to_have_title(re.compile(r".*Sign up"))
    hint_text = "A user with that username already exists."
    expect(page.get_by_text(hint_text)).to_be_visible()


def test_user_with_too_short_password_can_not_register(page: Page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.register(**{**REGISTERABLE_USER, **{"password": "1", "password_confirm": "1"}})
    expect(page).to_have_title(re.compile(r".*Sign up"))
    hint_text = "This password is too short. It must contain at least 8 characters."
    expect(page.get_by_text(hint_text)).to_be_visible()


# parameterize?
def test_user_with_invalid_user_name_can_not_register_dollar(page: Page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    home_page.register(**{**REGISTERABLE_USER, **{"username": "$"}})
    expect(page).to_have_title(re.compile(r".*Sign up"))
    hint_text = "Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters."
    expect(page.get_by_text(hint_text)).to_be_visible()


def test_shows_top_targets_in_descending_order(page: Page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    featured_targets = page.get_by_test_id("featured-target-element")
    NUMBER_OF_TOP_TARGETS = 4
    expect(featured_targets).to_have_count(NUMBER_OF_TOP_TARGETS)

    for _i, target_data in enumerate(TOP_TARGETS):
        target_name, coordinates, pk = target_data["name"], target_data["coordinates"], target_data["pk"]
        target = featured_targets.filter(has_text=re.compile(fr".*{target_name}.*"))

        expect(target).to_contain_text(target_name)

        ra, dec = coordinates
        expect(target).to_contain_text(f"RA {ra}")
        expect(target).to_contain_text(f"Dec {dec}")

        image_wrapper = target.get_by_test_id("galactic_thumbnail")
        expect(image_wrapper).to_have_attribute(
            "href", f"/targets/{pk}/"
        )

        image = target.locator("img")
        expect(image).to_have_attribute(
            "src",
            (
                "https://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&width=175"
                f"&height=175&fov=0.035&projection=TAN&coordsys=icrs&ra={ra}&dec={dec}&format=jpg"
            )
        )

        for link_data in BROKER_LINKS:
            title, href = link_data["title"], link_data["href"]
            link = target.get_by_title(title.format(target_name))
            expect(link).to_be_visible()
            expect(link).to_have_attribute(
                "href", href.format(target_name)
            )
        
        # all targets link
        all_targets_link = page.get_by_role("link", name="View all targets (with ranking)")
        expect(all_targets_link).to_be_visible()
        expect(all_targets_link).to_have_attribute("href", "/custom_code/prob_list.html")

        # footer
        footer_impressum_link = page.get_by_role("link", name="Impressum")
        expect(footer_impressum_link).to_be_visible()
        expect(footer_impressum_link).to_have_attribute("href", "https://www.uni-heidelberg.de/de/impressum")

        footer_imprint_link = page.get_by_role("link", name="Imprint")
        expect(footer_imprint_link).to_be_visible()
        expect(footer_imprint_link).to_have_attribute("href", "https://www.uni-heidelberg.de/en/imprint")

        footer_datenschutz = page.get_by_role("link", name="Datenschutzerklärung")
        expect(footer_datenschutz).to_be_visible()
        expect(footer_datenschutz).to_have_attribute("href", "https://www.uni-heidelberg.de/de/datenschutzerklaerung")

        footer_privacy = page.get_by_role("link", name="Privacy Statement")
        expect(footer_privacy).to_be_visible()
        expect(footer_privacy).to_have_attribute("href", "https://www.uni-heidelberg.de/en/privacy-statement")

def test_git_hash_is_visible(page: Page):
    home_page = HomePage(page, BASE_URL)
    home_page.open_it()
    commit_hash_container = home_page.get_commit_hash_container()
    expect(commit_hash_container).to_contain_text(re.compile(f"{os.environ.get('GIT_COMMIT')}"))
