from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from guardian.shortcuts import assign_perm
from custom_code.target_models import GalacticTarget

class Command(BaseCommand):
    help = 'Add all targets to the OPM users list'
    
    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True)

        for user in users:
            for target in GalacticTarget.objects.all():
                assign_perm('tom_targets.view_target', user, target)

