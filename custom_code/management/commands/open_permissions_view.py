from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from guardian.shortcuts import assign_perm
from custom_code.target_models import GalacticTarget

class Command(BaseCommand):
    help = 'Add all targets to the OPM users list'
    
    def handle(self, *args, **options):
        GalacticTarget.objects.all().update(permissions='PUBLIC')
    