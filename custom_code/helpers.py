from custom_code.target_models import ClassificationGeneralized, ClassificationSource


def create_and_attach_classifications_to_target(target, probabilities):
    sources, classifications_new, classifications_updated = [], [], []
    for prob in probabilities:
        classification_source, created_source = ClassificationSource.objects.get_or_create(
            classification_origin="ALeRCE_ZTF",
            classifier_name=prob["classifier_name"],
            class_name=prob["class_name"],
            classifier_version=prob["classifier_version"],
        )
        try:
            classification = ClassificationGeneralized.objects.get(
                target=target,
                source=classification_source,
                name=prob["class_name"]
            )
            classification.probability = prob["probability"]
            classification.save()
            created_classification = False
        except ClassificationGeneralized.DoesNotExist:
            classification = ClassificationGeneralized.objects.create(
                target=target,
                source=classification_source,
                name=prob["class_name"],
                probability=prob["probability"],
            )
            created_classification = True

        if created_source:
            sources.append(classification_source)
        if created_classification:
            classifications_new.append(classification)
        else:
            classifications_updated.append(classification)

    return sources, classifications_new, classifications_updated

