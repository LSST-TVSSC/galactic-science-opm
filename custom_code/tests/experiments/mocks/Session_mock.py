import json
import pickle
import pandas as pd


class Empty:
    pass





class SessionMock:
    def __init__(self) -> None:
        self.counter = 0
        self.step = 5
        self.pages = 2

    def request(self, *args, **kwargs):

        print(args)
        print(kwargs)
        response = Empty()
        response.status_code = 200

        with open("response_objects.json", "r") as jsonfile:
            data = json.load(jsonfile)

            def provide_result():
                if self.counter >= self.pages:
                    data["items"] = []
                    return data
                data["items"] = data["items"][
                    (self.counter * self.step) : ((self.counter + 1) * self.step)
                ]
                self.counter += 1
                return data

            response.json = provide_result
            return response

        with open("response_objects.json", "r") as jsonfile:
            data = json.load(jsonfile)

            def provide_result():
                if self.counter >= self.pages:
                    data["items"] = []
                    return data
                data["items"] = data["items"][
                    (self.counter * self.step) : ((self.counter + 1) * self.step)
                ]
                self.counter += 1
                return data

            response.json = provide_result
            return response
