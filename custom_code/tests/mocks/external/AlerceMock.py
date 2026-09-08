from os import path
import pickle
import pandas as pd


class AlerceMock:
    def __init__(self) -> None:
        self.counter = 0
        self.step = 5
        self.pages = 2

    def query_objects(self, *args, **kwargs):

        data_folder = path.join("custom_code", "tests", "mocks", "responses")
        ALERCE_QUERY_OBJECTS_PICKLE = path.join(
            data_folder, ("alerce__query_objects.pkl")
        )
        with open(ALERCE_QUERY_OBJECTS_PICKLE, "rb") as f:
            data = pickle.load(f)

            def provide_result():

                if self.counter >= self.pages:
                    df = pd.DataFrame([])
                    return df
                part_of_data = data[
                    (self.counter * self.step) : ((self.counter + 1) * self.step)
                ]
                self.counter += 1
                return part_of_data

            res = provide_result()
            return res
