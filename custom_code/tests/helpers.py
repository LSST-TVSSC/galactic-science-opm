from django.db import IntegrityError
import pickle


# written by claude
def assert_fields_equal(instance, expected):
    errors = []
    for field_name, expected_value in expected.items():
        actual_value = getattr(instance, field_name)
        if actual_value != expected_value:
            errors.append(
                f"{field_name}: expected {expected_value!r}, got {actual_value!r}"
            )
    assert not errors, "Mismatched fields:\n" + "\n".join(errors)

def instance_to_field_dict(instance, fields):
    return {f: getattr(instance, f) for f in fields}



# testing helper not written by claude
def assert_instances_match(expected, actual, fields_to_extract, key_to_match):
    found_counter = []
    for e in expected:
        corresponding_a = [
            a for a in actual if getattr(a, key_to_match) == getattr(e, key_to_match)
        ]
        assert len(corresponding_a) > 0, f"did not find matching element for {getattr(e, key_to_match)}"
        found_counter.append(getattr(e, key_to_match))
        corresponding_a = corresponding_a[0]
        expected_single = instance_to_field_dict(e, fields=fields_to_extract)
        assert_fields_equal(corresponding_a, expected_single)

    remaining = set([getattr(a, key_to_match) for a in actual]) - set(found_counter)
    assert len(remaining) == 0, f"Got elements that were not expected: {remaining}"



# helper for saving data to pickle
def make_pickle_from_data(filename, result):
    with open(filename, "wb") as f:
        pickle.dump(result, f)

def create_objects_update_or_create_raising_exception(EXPECTED_DATUMS, expected_exception):
    class ManagerMock():
        def __init__(self, expected_datums):
            self.call_counter = 0
            self.expected_datums = expected_datums

        def update_or_create(self, *args, **kwargs):
            if self.call_counter > 0:
                expected_exception()
            else:
                pass
            result =  self.expected_datums[self.call_counter], None
            self.call_counter += 1
            return result

    class ModelMock():
        def __init__(self, expected_datums):
            self.objects = ManagerMock(expected_datums)
    return ModelMock(EXPECTED_DATUMS)

def make_exception_to_be_raised(clazz, message):
    def wrapper():
        raise clazz(message)

    return wrapper

def create_raising_create_or_update(expected_datums, expected_exception):
    def wrapper():
        return create_objects_update_or_create_raising_exception(
            expected_datums, expected_exception
        )

    return wrapper

