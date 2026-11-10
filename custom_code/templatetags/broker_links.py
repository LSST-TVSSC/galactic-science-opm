from enum import Enum
from urllib.parse import quote

from django import template

register = template.Library()


class Survey(Enum):
    LSST = 1
    ZTF = 2
    UNKNOWN = 99


class Broker(Enum):
    ALERCE = 1
    ANTARES = 2
    FINK = 3
    UNKNOWN = 99


# Central place to define base URLs for brokers
BROKER_BASE_URLS = {
    Survey.LSST: {
        Broker.ALERCE: "https://lsst.alerce.online/object/",
        Broker.ANTARES: "https://antares.noirlab.edu/loci/lookup/",
    },
    Survey.ZTF: {
        Broker.FINK: "https://ztf.fink-portal.org/",
        Broker.ALERCE: "https://alerce.online/object/",
        Broker.ANTARES: "https://antares.noirlab.edu/loci/lookup/",
    },
    Survey.UNKNOWN: None,
}


def determine_survey(target_name):
    if "lsst" in target_name.lower():
        return Survey.LSST
    elif "ztf" in target_name.lower():
        return Survey.ZTF
    return Survey.UNKNOWN


def determine_broker(broker_key):
    try:
        return Broker[broker_key.upper()]
    except KeyError:
        return Broker.UNKNOWN


def get_basics_for_broker_links(broker_key, target_name):
    broker = determine_broker(broker_key)
    survey = determine_survey(target_name)
    base_survey = BROKER_BASE_URLS.get(survey)
    base_url = (base_survey or {}).get(broker)

    return broker, survey, base_url


def convert_internal_name_to_external(survey, name_internal):
    if survey == Survey.LSST:
        name = name_internal[5:]
    else:
        name = name_internal
    return name


def create_name(survey, broker, name, base_url):
    if survey == Survey.LSST and broker == Broker.ALERCE:
        return f"https://lsst.alerce.online/object/{name}?oid={name}&survey=lsst&page=1"
    return f"{base_url}{quote(name)}"


def make_url(broker_key, name_internal):
    broker, survey, base_url = get_basics_for_broker_links(broker_key, name_internal)
    if base_url is None:
        return None

    name = convert_internal_name_to_external(survey, name_internal)

    if not name:
        return None

    return create_name(survey, broker, name, base_url)


@register.simple_tag
def broker_target_url(broker_key, target):
    """
    Return a URL to view this target in the given broker.

    Parameters
    ----------
    broker : str
        Short broker key, e.g. "fink", "alerce", "antares".
    target : object
        Target instance, expected to have at least .name and possibly .ra/.dec.

    """

    name_internal = getattr(target, "name", "") or ""
    return make_url(broker_key, name_internal)


@register.simple_tag
def broker_alias_url(broker_key, ztf_alias):
    """
    Return a URL to view this target via its alias in the given broker.

    Parameters
    ----------
    broker : str
        Short broker key, e.g. "fink", "alerce", "antares".
    ztf_alias : str
        Alias of the target

    """

    name_internal = ztf_alias
    return make_url(broker_key, name_internal)
