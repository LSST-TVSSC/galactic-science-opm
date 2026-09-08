from alerce.core import Alerce
import pandas as pd

from astropy.time import Time, TimezoneInfo
from custom_code.photometry.PhotometryApiClient import PhotometryApiClient, PhotometryCandidate


class AlercePhotometryClient(PhotometryApiClient):
    def fetch_photometry_for_targets(self, targets, survey):
        results = []
        alerce = Alerce()
        filter_definition = {1: "ZTF_g", 2: "ZTF_r", 3: "ZTF_i"}
        for target in targets:
            ALERCE_name = target.name
            detections_photometry = alerce.query_detections(
                ALERCE_name, format="pandas", survey=survey
            )

            # remove multiple detections
            detections_photometry = detections_photometry.drop_duplicates(subset="mjd")
            forced_photometry = alerce.query_forced_photometry(
                ALERCE_name, format="pandas", survey=survey
            )

            # iterate over detections and make candidates
            for i, row in detections_photometry.iterrows():
                jd = Time(row["mjd"], format="mjd", scale="utc")
                jd.to_datetime(timezone=TimezoneInfo())
                timestamp = jd.to_datetime(timezone=TimezoneInfo())
                if "magpsf_corr" in detections_photometry.columns:
                    if not pd.isna(row["magpsf_corr"]) and row["magpsf_corr"] < 100.0:
                        candidate = PhotometryCandidate(
                            magnitude=row["magpsf_corr"],
                            filter=filter_definition[row["fid"]],
                            error=row["sigmapsf_corr_ext"],
                            timestamp=timestamp,
                            location=target.name,
                            source="ALERCE",
                        )
                        results.append(candidate)

            # iterate over forced and make candidates
            for i, row in forced_photometry.iterrows():
                jd = Time(row["mjd"], format="mjd", scale="utc")
                jd.to_datetime(timezone=TimezoneInfo())
                timestamp = jd.to_datetime(timezone=TimezoneInfo())
                if "magpsf_corr" in detections_photometry.columns:
                    if not pd.isna(row["mag_corr"]) and row["mag_corr"] < 100.0:
                        candidate = PhotometryCandidate(
                            magnitude=row["mag_corr"],
                            filter=filter_definition[row["fid"]],
                            error=row["e_mag_corr_ext"],
                            timestamp=timestamp,
                            location=target.name,
                            source="ALERCE",
                        )
                        results.append(candidate)

            return results
