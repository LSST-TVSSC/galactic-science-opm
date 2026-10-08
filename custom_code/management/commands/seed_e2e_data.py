from os import path

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core import management
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse

from galactic_science_opm.settings import BASE_DIR, env


class Command(BaseCommand):
    def handle(self, *args, **options):

        if not settings.TESTING:
            raise management.CommandError(
                "seed_e2e_data may only run in the test environment"
            )

        missing = [v for v in ("E2E_ADMIN_PASSWORD", "E2E_USER_PASSWORD") if not env(v)]
        if missing:
            raise management.CommandError(
                f"Missing environment variables: {', '.join(missing)}"
            )

        _ = management.call_command("flush", "--noinput")
        _ = management.call_command("migrate", "--noinput")
        _ = management.call_command(
            "loaddata", path.join(BASE_DIR, "test_data", "db_out_full.json")
        )

        superuser = User.objects.create_superuser(
            username="admin",
            password=env("E2E_ADMIN_PASSWORD"),
            email="admin@example.com",
        )

        public_group = Group.objects.create(name="Public")
        public_group.save()

        unapproved_test_user = register_test_user("max", public_group)
        approve_user(superuser, unapproved_test_user, public_group)


def register_test_user(username, group):
    USER_PW = env("E2E_USER_PASSWORD")
    user_data = {
        "username": username,
        "first_name": "m",
        "last_name": "k",
        "email": "mk@example.com",
        "password1": USER_PW,
        "password2": USER_PW,
        "groups": [group.id],
    }

    form_data = {
        "profile-TOTAL_FORMS": ["1"],
        "profile-INITIAL_FORMS": ["0"],
        "profile-0-affiliation": ["qa"],
        "profile-0-id": [""],
        "profile-0-user": [""],
    }

    user_form_data = {
        **user_data,
        **form_data,
    }

    client = Client()
    _ = client.post(
        reverse("registration:register"),
        data=user_form_data,
    )
    user = User.objects.get(username=user_data["username"])
    return user


def approve_user(superuser, user_to_approve, users_group):
    form_data_super = {
        "profile-TOTAL_FORMS": ["1"],
        "profile-INITIAL_FORMS": ["1"],
        "profile-MIN_NUM_FORMS": ["0"],
        "profile-MAX_NUM_FORMS": ["1"],
        "profile-0-affiliation": ["qa"],
        "profile-0-id": [str(user_to_approve.profile.id)],
        "profile-0-user": [str(user_to_approve.id)],
    }
    user_data_super = {
        "username": "max",
        "first_name": "m",
        "last_name": "k",
        "email": "mk@example.com",
        "groups": [users_group.id],
    }
    user_form_data_super = {
        **user_data_super,
        **form_data_super,
    }
    client = Client()
    client.force_login(superuser)
    _ = client.post(
        reverse("registration:approve", kwargs={"pk": user_to_approve.id}),
        data=user_form_data_super,
    )
