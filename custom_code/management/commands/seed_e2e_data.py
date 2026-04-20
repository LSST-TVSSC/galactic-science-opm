import json
from os import path, remove
from django.core import management
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from galactic_science_opm.settings import BASE_DIR

class Command(BaseCommand):
    def handle(self, *args, **options):

        User.objects.create_superuser(username="admin", password="1234", email="admin@example.com")
        User.objects.create_user(username="max", password="tests")

        with open(path.join(BASE_DIR, "custom_code", "tests", "e2e", "db_out.json"), encoding="utf-8") as f:
            read_data = f.read()

        as_json = json.loads(read_data)
        for entry in as_json:
            if entry["model"] != "tom_targets.basetarget":
                continue
            
            # just to demonstrate how to change seed data before importing it.
            entry["fields"]["name"] += "_modify"

        with open(path.join(BASE_DIR, "custom_code", "tests", "e2e", "temp_seed_out.json"), encoding="utf-8", mode="w+") as f:
            f.write(json.dumps(as_json))

        _ = management.call_command(
            "loaddata",
            'custom_code/tests/e2e/temp_seed_out.json'
        )

        remove(path.join(BASE_DIR, "custom_code", "tests", "e2e", "temp_seed_out.json"))
        

