from django import template
from django.utils.safestring import mark_safe
from astropy.time import Time
from custom_code.target_models import MicrolensingParameterModel

register = template.Library()


def make_target_tags_list(target):
    tags = list()
    DAYS_CUTOFF = 5

    if target["age_days"] < DAYS_CUTOFF:
        tags.append({
            "class": "new",
            "text": f"Created less than {DAYS_CUTOFF} days ago"
        })

    if target["object"].metric_bogus > 0.6:
        tags.append({
            "class": "bogus",
            "text": "bogus metric > 0.6"
        })
    target_radar = target["object"].target  
    params = (MicrolensingParameterModel.objects
          .filter(target=target_radar)
          .order_by("-updated_at")
          .only("t0", "tE")
          .first())

    t0 = tE = None
    if params is not None:
        if params.t0 is not None:
            t0 = params.t0 + 2450000.
        tE = params.tE
    if t0 is not None and tE is not None:
        try:
            current_jd = Time.now().jd
            if float(t0) - float(tE) < current_jd < float(t0) + float(tE):
                tags.append({"class": "active", "text": "Microlensing event current t in [t0-tE,t0+tE]"})
        except (ValueError, TypeError):
            pass

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
        elif tag["class"] == "active":
            elements.append(f"<div title='{tag['text']}' class='target-tag' style='background-color: orange; color: white; border-color: orange;'>{tag['class']}</div>")
        else:
            elements.append(f"<div title='{tag['text']}' class='target-tag' >{tag['class']}</div>")



    return mark_safe("".join(elements))
