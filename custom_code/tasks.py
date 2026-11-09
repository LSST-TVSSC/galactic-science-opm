import csv
from io import StringIO

from celery import shared_task
from django.contrib.auth.models import Group
from tom_targets.models import Target, TargetName, User

from custom_code.target_models import (
    ClassificationGeneralized,
    ClassificationSource,
    CompactBinariesRadarData,
    GalacticTarget,
    MicrolensingRadarData,
)


@shared_task
def upload_csv(target_stream, user_id):
    print("csv_import: Starting import")
    user = User.objects.get(id=user_id)
    print("csv_import: Creating targets")
    result = custom_import_targets(target_stream=target_stream["data"])
    print("csv_import: Done creating targets")
    print("csv_import: Applying access rights")
    targets = GalacticTarget.objects.in_bulk(result["targets"])
    for target in targets.values():
        target.give_user_access(user)
    print("csv_import: Import done")
    return result


def custom_import_targets(target_stream):
    """
    mkistner: This was adapted from tom_targets/utils.py import_targets

    Imports a set of targets into the TOM and saves them to the database.

    :param target_stream: String buffer of targets
    :type target_stream: StringIO

    :returns: dictionary of successfully imported targets, as well errors
    :rtype: dict
    """
    targetreader = csv.DictReader(StringIO(target_stream), dialect=csv.excel)
    targets = []
    errors = []

    class CsvImportError(Exception): ...

    class MissingGroupError(Exception): ...

    supported_fields = (
        "name",
        "name2",
        "type",
        "ra",
        "dec",
        "groups",
        "probability",
        "class_name",
        "classifier_version",
        "expected_visits",
        "target_type",
    )
    base_target_fields = [field.name for field in Target._meta.get_fields()]
    has_found_header = False
    has_looped_once = False
    for index, row in enumerate(targetreader):
        # filter out empty values in base fields, otherwise converting empty
        # string to float will throw error
        row = {
            k: v for (k, v) in row.items() if not (k in base_target_fields and not v)
        }
        target_extra_fields = []
        target_names = []
        group_names = []
        target_fields = {}

        probability = None
        class_name = None
        classifier_version = None
        expected_visits = None
        target_type = None
        groups_value = ""

        for k in row:
            if k != "name" and k.startswith("name"):
                target_names.append(row[k])
            elif k == "groups":
                groups_value = row[k]
                groups = groups_value.split(",")
                has_found_header = True
                for group in groups:
                    group_names.append(group.strip())
            elif k in base_target_fields:
                target_fields[k] = row[k]
                has_found_header = True
            elif k not in supported_fields:
                target_extra_fields.append((k, row[k]))

            if k == "probability":
                probability = row[k]
            elif k == "class_name":
                class_name = row[k]
            elif k == "classifier_version":
                classifier_version = row[k]
            elif k == "expected_visits":
                expected_visits = row[k]
            elif k == "target_type":
                target_type = row[k]

        has_looped_once = True
        try:
            if not has_found_header or not row:
                raise CsvImportError(
                    "Missing header in csv file. Please check the example file, adapt your file accordingly and try again."
                )
            if groups_value == "":
                raise MissingGroupError(
                    "At least one group needs to be provided, e.g. 'Public'"
                )

            target = Target.objects.create(**target_fields)
            for name in target_names:
                if name:
                    TargetName.objects.create(target=target, name=name)
            targets.append(target)
            for group in group_names:
                try:
                    group_instance = Group.objects.get(name=group)
                    target.give_user_access(group_instance)
                except Group.DoesNotExist:
                    pass
            if (
                probability
                and class_name
                and classifier_version
                and expected_visits
                and target_type
            ):
                classification_name = "n.a."
                target_type__pretty = "tbd"

                if target_type == "microlensing":
                    classification_name = "microlensing"
                    target_type__pretty = "Microlensing candidate"
                    _ = MicrolensingRadarData.objects.create(
                        target=target, average_master_probability=probability
                    )
                elif target_type == "compact_binary":
                    classification_name = "compact_binary"
                    target_type__pretty = "CV/Nova candidate"
                    _ = CompactBinariesRadarData.objects.create(
                        target=target, average_master_probability=probability
                    )
                target.target_type = target_type__pretty
                target.save()

                classification_source, _created_source = (
                    ClassificationSource.objects.get_or_create(
                        classification_origin="uploaded",
                        classifier_name="uploaded",
                        class_name=class_name,
                        classifier_version=classifier_version,
                    )
                )
                try:
                    classification = ClassificationGeneralized.objects.get(
                        target=target,
                        source=classification_source,
                        name=classification_name,
                    )
                    classification.probability = probability
                    classification.save()
                except ClassificationGeneralized.DoesNotExist:
                    classification = ClassificationGeneralized.objects.create(
                        target=target,
                        source=classification_source,
                        name=classification_name,
                        probability=probability,
                    )

        except Exception as e:
            if not has_found_header:
                error = str(e)
                errors.append(error)
                break
            else:
                error = f"Error on line {index + 2}: {e!s}"
                errors.append(error)

    if not has_looped_once:
        error = "Could not find rows. Have you provided a header?"
        errors.append(error)

    return {"targets": [target.id for target in targets], "errors": errors}
