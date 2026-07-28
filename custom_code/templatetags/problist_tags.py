from django import template
from django.utils.safestring import mark_safe

register = template.Library()


def make_target_tags_list(target):
    tags = list()
    DAYS_CUTOFF = 3

    if target["age_days"] < DAYS_CUTOFF:
        tags.append({
            "class": "new",
            "text": f"Created less than {DAYS_CUTOFF} days ago"
        })

    if target["object"].metric_bogus > 0.5:
        tags.append({
            "class": "bogus",
            "text": "bogus metric > 0.5"
        })


    return tags

@register.simple_tag
def target_tags_list(target):
    tags = make_target_tags_list(target)
    just_classes = [tag["class"] for tag in tags]
    return " ".join(just_classes)

@register.simple_tag
def target_tags_elements(target):
    tags = make_target_tags_list(target)
    elements = list()
    
    bad_tags = ("bogus",)
    for tag in tags:
        if tag["class"] in bad_tags:
            elements.append(f"<div title='{tag['text']}' class='target-tag bad'>{tag['class']}</div>")
        else:
            elements.append(f"<div title='{tag['text']}' class='target-tag' >{tag['class']}</div>")

    return mark_safe("".join(elements))


