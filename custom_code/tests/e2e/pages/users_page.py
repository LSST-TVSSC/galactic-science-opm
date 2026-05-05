from playwright.sync_api import Page, expect

class UsersPage:
    def __init__(self, page: Page, base_url) -> None:
        self.page = page
        self.base_url = base_url

    def open_it(self):
        self.page.goto(f"{self.base_url}/users/")
    
    def login(self, username, password):
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("Password").fill(password)
        self.page.get_by_role("button", name="Login").click()

    def logout(self):
        logout_button = self._get_logout_button()
        logout_button.click()

    def open_profile(self, username):
        profile_link = self.page.get_by_role("link", name=username)
        profile_link.click()

    def _get_logout_button(self):
        return self.page.get_by_role("button", name="Logout")

    def user_is_logged_in(self):
        logout_button = self._get_logout_button()
        expect(logout_button).to_be_visible()

    def user_is_logged_out(self):
        logout_button = self._get_logout_button()
        expect(logout_button).not_to_be_visible()

    def get_pending_users_table(self):
        return self.page.get_by_test_id("pending-users")

    # These are very brittle...
    def get_groups_table(self):
        return self.page.get_by_role("columnheader", name="Members").locator('xpath=../../..')
    
    # These are very brittle...
    def get_active_users_table(self):
        return self.page.get_by_role("columnheader", name="Change Password").locator('xpath=../../..')

    def get_number_of_pending_users(self):
        table = self.get_pending_users_table()
        rows = table.locator("tbody tr")
        return rows.count()

    def get_number_of_groups(self):
        table = self.get_groups_table()
        rows = table.locator("tbody tr")
        return rows.count()

    def get_number_of_active_users(self):
        table = self.get_active_users_table()
        rows = table.locator("tbody tr")
        return rows.count()

    def register(self, username, first_name, last_name, email, password, password_confirm, affiliation):
        self.page.get_by_text("Register").click()
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("First name").fill(first_name)
        self.page.get_by_placeholder("Last name").fill(last_name)
        self.page.get_by_placeholder("Email").fill(email)
        self.page.get_by_placeholder("Password", exact=True).fill(password)
        self.page.get_by_placeholder("Password confirmation").fill(password_confirm)
        self.page.get_by_placeholder("Affiliation").fill(affiliation)
        self.page.get_by_role("button", name="Register").click()

    def approve(self, username):
        self.page.get_by_role("link", name="Users").click()
        table = self.get_pending_users_table()
        row = table.get_by_role("cell", name=username).locator('xpath=..')
        row.get_by_role("link", name="Approve").click()
        self.page.get_by_role("button", name="Approve").click()

    def delete_pending_user(self, username):
        self.page.get_by_role("link", name="Users").click()
        table = self.get_pending_users_table()
        row = table.get_by_role("cell", name=username).locator('xpath=..')
        row.get_by_role("link", name="Delete").click()
        self.page.get_by_role("button", name="Confirm").click()

