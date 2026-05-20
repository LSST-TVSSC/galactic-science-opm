from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, MicrolensingRadarData
from custom_code.brokers import alerce_ztf
import numpy as np
from astropy import units as u

class Command(BaseCommand):

    help = 'Populate the database with lightcurves of ALeRCE ZTF microlensing candidates'

    def add_arguments(self, parser):
        parser.add_argument('event_name', help='Either event name or substring the events should contain')
        parser.add_argument('n_event_pages', help='Number of events to be ingested, = number of pages')
        parser.add_argument('days', help='days firstmjd before now')
        parser.add_argument('--phot', help='Force ingest of full photometry [optional]: True or False')

    def handle(self, *args, **options):
        print('Starting ALeRCE photometry ingest')
        Alerce = alerce_ztf.ALERCEBroker()
        full_phot = False
        if options['phot'] == str(True):
            full_phot = True
        # If a number of events to select is given, make a list of all available events;
        # the random selection is applied later.  If a specific event name is given, fetch data for that event only
        (list_of_targets, new_targets) = Alerce.fetch_alerts(events=int(str(options['n_event_pages'])),
                                                             days=int(str(options['days'])))
        print('Identified '+str(len(list_of_targets))+' target(s) from ALeRCE')
        list_of_targets = [x for x in list_of_targets if str(options['event_name']) in x.name ] 
        new_targets = [x for x in new_targets if str(options['event_name']) in x.name ]
        if full_phot:
            Alerce.find_and_ingest_photometry(list_of_targets)
        else:
            Alerce.find_and_ingest_photometry(new_targets)
            
        print('Filtered and Identified '+str(len(list_of_targets))+' target(s) from ALeRCE')
        print('Completed run of ALeRCE event ingest')
        print('Update photometry of 50 priority targets')
        distinct_ids = MicrolensingRadarData.objects.order_by('target_id', '-updated_at').distinct('target_id').filter(target__name__icontains='ZTF').filter(average_master_probability__gt=0.)
        qs = MicrolensingRadarData.objects.filter(id__in=distinct_ids).order_by('-average_master_probability').distinct()[:50]                
        priority_targets = [GalacticTarget.objects.filter(name__icontains=target.target.name).last() for target in qs]
        try:
            Alerce.find_and_ingest_photometry(priority_targets)
        except Exception as e:
            print(f"Unexpected exception {e}")
        print("Update priority targets complete.")