import pickle


class VizierMock:
    def query_region(self, *args, **kwargs):
        VIZIER_QUERY_REGION_PICKLE = (
            "custom_code/tests/mocks/external/tablelist_for_Vizier.query_region_ZTF21abasvhl.pkl"
        )
        with open(VIZIER_QUERY_REGION_PICKLE, "rb") as f:
            result = pickle.load(f)
        return result

