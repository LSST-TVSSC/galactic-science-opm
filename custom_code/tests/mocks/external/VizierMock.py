from os import path
import pickle


class VizierMock:
    def query_region(self, *args, **kwargs):
        data_folder = path.join("custom_code", "tests", "mocks", "external")
        VIZIER_QUERY_REGION_PICKLE = path.join(
            data_folder,
            "tablelist_for_Vizier.query_region_ZTF21abasvhl.pkl",
        )
        with open(VIZIER_QUERY_REGION_PICKLE, "rb") as f:
            result = pickle.load(f)
        return result
