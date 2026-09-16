from django.test import TestCase

from custom_code.helpers import greet_user


class TestHelpers(TestCase):
    def test_should_greet_informally(self):
        result = greet_user("Foo", "Bar")
        self.assertEqual(result, "Hey there, Foo! How's it hangin'?")

    def test_should_greet_formally(self):
        result = greet_user("Foo", "formal")
        self.assertEqual(result, "Good day, Foo! How may I help you today?")
