from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe

from custom_code.target_models import (
    Classification,
    CompactBinariesRadarData,
)

register = template.Library()


def make_target_tags_list(target):
    tags = []
    DAYS_CUTOFF = 5

    if target["age_days"] < DAYS_CUTOFF:
        tags.append(
            {"class": "new", "text": f"Created less than {DAYS_CUTOFF} days ago"}
        )

    if target["object"].metric_bogus > 0.6:
        tags.append({"class": "bogus", "text": "bogus metric > 0.6"})

    return tags


@register.filter
def microlensing_radar_by_name(name):
    try:
        return CompactBinariesRadarData.objects.filter(target=name).latest()
    except ObjectDoesNotExist:
        return None


@register.filter
def classification_by_name(name):
    try:
        return Classification.objects.get(target=name).latest()
    except ObjectDoesNotExist:
        return None


@register.simple_tag
def target_tags_list(target):
    tags = make_target_tags_list(target)
    just_classes = [tag["class"] for tag in tags]
    return " ".join(just_classes)


@register.simple_tag
def target_tags_elements(target):
    tags = make_target_tags_list(target)
    elements = []

    bad_tags = ("bogus",)
    for tag in tags:
        if tag["class"] in bad_tags:
            elements.append(
                f"<div title='{tag['text']}' class='target-tag bad'>{tag['class']}</div>"
            )
        else:
            elements.append(
                f"<div title='{tag['text']}' class='target-tag' >{tag['class']}</div>"
            )

    return mark_safe("".join(elements))
