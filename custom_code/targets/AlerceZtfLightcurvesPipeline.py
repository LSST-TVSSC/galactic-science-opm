
class AlerceZtfLightcurvesPipeline:
    def __init__(
        self,
        target_api_client,
        target_creator,
        glade_api_client,
        visits_checker,
        variability_checker,
        photometry_fetcher,
        photometry_creator,
        logger
    ):
        self.target_api_client = target_api_client
        self.target_creator = target_creator
        self.glade_api_client = glade_api_client
        self.visits_api_client = visits_checker
        self.variability_api_client = variability_checker
        self.photometry_api_client = photometry_fetcher
        self.photometry_creator = photometry_creator
        self.logger = logger

    def run(self, class_names, since_n_days, start_date, survey, fetch_photometry_for_all_targets, event_name=None):

        START_DATE = start_date
        SURVEY = survey
        CLASS_NAMES = class_names
        DAYS = since_n_days

        # get target candidates for all classes (currently probably Microlensing and CV/Nova)
        target_candidates = []
        for class_name in CLASS_NAMES:
            target_candidates_for_class = self.target_api_client.fetch_potential_targets(
                survey=SURVEY,
                class_name=class_name,
                since_n_days=DAYS,
                start_date=START_DATE,
            )
            target_candidates += target_candidates_for_class
        self.logger("success", f"Found {len(target_candidates)} potential targets.")

        # filter according to event_name
        filtered_candidates = target_candidates
        if event_name:
            filtered_candidates = [x for x in target_candidates if event_name in x["name"]]
            pass

        self.logger("success", f"{len(filtered_candidates)} potential targets remaining after filtering.")
        
        # create targets from candidates
        all_targets, new_targets = self.target_creator.create_targets_from_candidates(
            filtered_candidates
        )
        self.logger("success", f"{len(new_targets)} targets created.")

        if new_targets:
            # make new targets public
            self.target_creator.make_targets_public(new_targets)
            self.logger("success", f"Targets are now public.")

            # fetch and update glade info
            glade_info = self.glade_api_client.check_glade_plus_for_targets(new_targets)
            self.target_creator.update_known_extragalactic(new_targets, glade_info)
            self.logger("success", f"Targets received glade info.")

            # fetch and update expected visits for new targets
            visits_info = self.visits_api_client.get_expected_visits_for_targets(
                new_targets
            )
            self.target_creator.update_expected_visits(new_targets, visits_info)
            self.logger("success", f"Targets received expected visits info.")

            # fetch and update known_variability
            variability_info = self.variability_api_client.get_variability_info_for_targets(
                new_targets
            )
            self.target_creator.update_known_variability(new_targets, variability_info)
            self.logger("success", f"Targets received variability info.")

        targets_needing_photometry = new_targets

        if fetch_photometry_for_all_targets:
            targets_needing_photometry = all_targets

        PRIO_COUNT = 50
        priority_targets = self.target_creator.get_priority_targets(PRIO_COUNT, survey)
        targets_needing_photometry = targets_needing_photometry + priority_targets

        # fetch photometry for relevant targets
        if targets_needing_photometry:
            photometry_data = self.photometry_api_client.fetch_photometry_for_targets(
                targets_needing_photometry, survey=SURVEY
            )
            self.logger("success", f"Photometry for targets fetched")

            # create photometry
            errors, _ = self.photometry_creator.create_photometry_for_targets(photometry_data)
            if errors:
                self.logger("error", errors)
            self.logger("success", f"Photometry for targets created")


