import datetime
from unittest import TestCase
from astropy.time import Time, TimezoneInfo
import pandas as pd
import numpy as np
pd.set_option('future.no_silent_downcasting', True)

# A possible implementation. Should go into different container.
def alerce_photometry_converter(target_name, detections_photometry):
    results = []
    filter_definition = {1: "ZTF_g", 2: "ZTF_r", 3: "ZTF_i"}
    for _, row in detections_photometry.iterrows():
        jd = Time(row["mjd"], format="mjd", scale="utc")
        jd.to_datetime(timezone=TimezoneInfo())
        if "magpsf_corr" not in detections_photometry.columns:
            continue
        if not pd.isna(row["magpsf_corr"]) and row["magpsf_corr"] < 100.0:
            datum = {
                "magnitude": row["magpsf_corr"],
                "filter": filter_definition[row["fid"]],
                "error": row["sigmapsf_corr_ext"],
            }
            dto = {
                "timestamp": jd.to_datetime(timezone=TimezoneInfo()),
                "value": datum,
                "source_name": "ALERCE",
                "source_location": target_name,
                "data_type": "photometry",
            }
            results.append(dto)

    return results


class AlercePhotometryConverterTests(TestCase):

    def test_converts_alerce_photometry_to_dto_all_good(self):
        self.maxDiff = 1000
        TARGET_NAME_TO_TEST = "ZTF26aarbgfh"
        # converted from an API response
        alerce_data_as_dict = {
            "tid": {0: "ztf"},
            "mjd": {0: 61105.53785880003},
            "candid": {0: "3351537854115015018"},
            "fid": {0: 2},
            "pid": {0: 3351537854115},
            "diffmaglim": {0: 19.6387},
            "isdiffpos": {0: 1},
            "nid": {0: 3351},
            "distnr": {0: 0.120913},
            "magpsf": {0: 16.5425},
            "magpsf_corr": {0: 15.695387},
            "magap": {0: 16.71},
            "sigmapsf": {0: 0.071727},
            "sigmapsf_corr": {0: 0.029953785},
            "sigmapsf_corr_ext": {0: 0.03287286},
            "sigmagap": {0: 0.0259},
            "ra": {0: 274.5777789},
            "dec": {0: 2.0569714},
            "rb": {0: 0.851429},
            "rbversion": {0: "t17_f5_c3"},
            "magapbig": {0: 16.7124},
            "sigmagapbig": {0: 0.0325},
            "has_stamp": {0: False},
            "corrected": {0: True},
            "dubious": {0: False},
            "step_id_corr": {0: "27.5.7a32.dev1"},
            "phase": {0: 0.0},
            "parent_candid": {0: 3.381400920515015e18},
            "drb": {0: None}, # this was nan
            "rfid": {0: None}, # this was nan
        }
        expected = [
            {
                "timestamp": datetime.datetime(2026, 3, 6, 12, 54, 31, 323, tzinfo=TimezoneInfo()),
                "value": {
                    "magnitude": 15.695387,
                    "filter": "ZTF_r",
                    "error": 0.03287286,
                },
                "source_name": "ALERCE",
                "source_location": "ZTF26aarbgfh",
                "data_type": "photometry",
            }
        ]
        alerce_photometry = pd.DataFrame.from_dict(alerce_data_as_dict).fillna(value=np.nan)
        converted = alerce_photometry_converter(TARGET_NAME_TO_TEST, alerce_photometry)
        self.assertCountEqual(expected, converted)
    
    def test_skips_alerce_photometry_when_magpsf_corr_is_missing(self):
        TARGET_NAME_TO_TEST = "ZTF26aarbgfh"
        alerce_data_as_dict = {
            "tid": {0: "ztf"},
            "mjd": {0: 61105.53785880003},
            "candid": {0: "3351537854115015018"},
            "fid": {0: 2},
            "pid": {0: 3351537854115},
            "diffmaglim": {0: 19.6387},
            "isdiffpos": {0: 1},
            "nid": {0: 3351},
            "distnr": {0: 0.120913},
            "magpsf": {0: 16.5425},
            "magap": {0: 16.71},
            "sigmapsf": {0: 0.071727},
            "sigmapsf_corr": {0: 0.029953785},
            "sigmapsf_corr_ext": {0: 0.03287286},
            "sigmagap": {0: 0.0259},
            "ra": {0: 274.5777789},
            "dec": {0: 2.0569714},
            "rb": {0: 0.851429},
            "rbversion": {0: "t17_f5_c3"},
            "magapbig": {0: 16.7124},
            "sigmagapbig": {0: 0.0325},
            "has_stamp": {0: False},
            "corrected": {0: True},
            "dubious": {0: False},
            "step_id_corr": {0: "27.5.7a32.dev1"},
            "phase": {0: 0.0},
            "parent_candid": {0: 3.381400920515015e18},
            "drb": {0: None}, # this was nan
            "rfid": {0: None}, # this was nan
        }
        expected = []
        alerce_photometry = pd.DataFrame.from_dict(alerce_data_as_dict).fillna(value=np.nan)
        converted = alerce_photometry_converter(TARGET_NAME_TO_TEST, alerce_photometry)
        self.assertEquals(expected, converted)

    def test_skips_alerce_photometry_for_magpsf_corr_greater_than_100(self):
        TARGET_NAME_TO_TEST = "ZTF26aarbgfh"
        alerce_data_as_dict = {
            "tid": {0: "ztf"},
            "mjd": {0: 61105.53785880003},
            "candid": {0: "3351537854115015018"},
            "fid": {0: 2},
            "pid": {0: 3351537854115},
            "diffmaglim": {0: 19.6387},
            "isdiffpos": {0: 1},
            "nid": {0: 3351},
            "distnr": {0: 0.120913},
            "magpsf": {0: 16.5425},
            "magpsf_corr": {0: 100.695387},
            "magap": {0: 16.71},
            "sigmapsf": {0: 0.071727},
            "sigmapsf_corr": {0: 0.029953785},
            "sigmapsf_corr_ext": {0: 0.03287286},
            "sigmagap": {0: 0.0259},
            "ra": {0: 274.5777789},
            "dec": {0: 2.0569714},
            "rb": {0: 0.851429},
            "rbversion": {0: "t17_f5_c3"},
            "magapbig": {0: 16.7124},
            "sigmagapbig": {0: 0.0325},
            "has_stamp": {0: False},
            "corrected": {0: True},
            "dubious": {0: False},
            "step_id_corr": {0: "27.5.7a32.dev1"},
            "phase": {0: 0.0},
            "parent_candid": {0: 3.381400920515015e18},
            "drb": {0: None}, # this was nan
            "rfid": {0: None}, # this was nan
        }
        expected = []
        alerce_photometry = pd.DataFrame.from_dict(alerce_data_as_dict).fillna(value=np.nan)
        converted = alerce_photometry_converter(TARGET_NAME_TO_TEST, alerce_photometry)
        self.assertEquals(expected, converted)
