import json
from os import path, remove
from django.core import management
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from django.test import Client
from django.urls import reverse

from galactic_science_opm.settings import BASE_DIR

class Command(BaseCommand):
    
    def handle(self, *args, **options):

        with open(
            path.join(BASE_DIR, "custom_code", "tests", "e2e", "data", "db_out_full.json"),
            encoding="utf-8",
        ) as f:
            read_data = f.read()

        as_json = json.loads(read_data)
        for entry in as_json:
            if entry["model"] != "tom_targets.basetarget":
                continue
            
            # just to demonstrate how to change seed data before importing it.
            entry["fields"]["name"] += ""

        with open(path.join(BASE_DIR, "custom_code", "tests", "e2e", "temp_seed_out.json"), encoding="utf-8", mode="w+") as f:
            f.write(json.dumps(as_json))

        _ = management.call_command(
            "loaddata",
            'custom_code/tests/e2e/temp_seed_out.json'
        )

        remove(path.join(BASE_DIR, "custom_code", "tests", "e2e", "temp_seed_out.json"))

        superuser = User.objects.create_superuser(username="admin", password="1234", email="admin@example.com")

        public_group = Group.objects.create(name="Public")
        public_group.save()

        unapproved_test_user = register_test_user("max", public_group)
        approve_user(superuser, unapproved_test_user, public_group)


def register_test_user(username, group):

    user_data = {
        'username': username,
        'first_name': 'm',
        'last_name': 'k',
        'email': 'mk@example.com',
        'password1': '1234!!!!',
        'password2': '1234!!!!',
        'groups': [group.id],
    }

    form_data = {
        'profile-TOTAL_FORMS': ["1"],
        'profile-INITIAL_FORMS': ["0"],
        'profile-0-affiliation': ["qa"],
        'profile-0-id': [""],
        'profile-0-user': [""],
    }
    
    user_form_data = {
        **user_data,
        **form_data,
    }
    
    client = Client()
    _ =client.post(
        "http://localhost:8000" + reverse('registration:register'), 
        data=user_form_data,
    )
    user = User.objects.get(username=user_data['username'])
    return user

def approve_user(superuser, user_to_approve, users_group):
    form_data_super = {
        'profile-TOTAL_FORMS': ["1"],
        'profile-INITIAL_FORMS': ["1"],
        'profile-MIN_NUM_FORMS': ["0"],
        'profile-MAX_NUM_FORMS': ["1"],
        'profile-0-affiliation': ["qa"],
        'profile-0-id': ["3"],
        'profile-0-user': ["3"],
    }
    user_data_super = {
        'username': 'max',
        'first_name': 'm',
        'last_name': 'k',
        'email': 'mk@example.com',
        'groups': [users_group.id],
    }
    user_form_data_super = {
        **user_data_super,
        **form_data_super,
    }
    client = Client()
    client.force_login(superuser)
    _ = client.post(
        "http://localhost:8000" + reverse('registration:approve', kwargs={'pk': user_to_approve.id}), 
        data=user_form_data_super
    )
