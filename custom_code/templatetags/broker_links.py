from django import template
from urllib.parse import quote

register = template.Library()

# Central place to define base URLs for brokers
BROKER_BASE_URLS = {
    "fink": "https://fink-broker.org/",
    "alerce": "https://alerce.online/",
    "antares": "https://antares.noirlab.edu/loci",
}


@register.simple_tag
def broker_target_url(broker, target):
    """
    Return a URL to view this target in the given broker.

    Parameters
    ----------
    broker : str
        Short broker key, e.g. "fink", "alerce", "antares".
    target : object
        Target instance, expected to have at least .name and possibly .ra/.dec.

    NOTE: This is intentionally simple and should be updated once
    the final broker query patterns are known. Templates only need
    to call this tag; they won't change.
    """
    broker_key = (broker or "").lower()
    base = BROKER_BASE_URLS.get(broker_key)
    if not base:
        return ""

    if target is None:
        return base

    # For now, just use the target name as a generic query parameter.
    # Later, update this to use the official broker API format
    # (e.g. by name, or RA/Dec, or internal ID, whatever).
    name = getattr(target, "name", "") or ""
    ra = getattr(target, "ra", None)
    dec = getattr(target, "dec", None)

    # --- DEFAULT BEHAVIOUR ---
    # Simple pattern using name; safe to change later without touching templates.
    if name:
        return f"{base}?q={quote(name)}"

    # If name is missing but we have coordinates, we could fall back to that.
    if ra is not None and dec is not None:
        return f"{base}?ra={ra}&dec={dec}"

    # Define whetever else might be needed here
    
    # Fallback: just the broker homepage
    return base

