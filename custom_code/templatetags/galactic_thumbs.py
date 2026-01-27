from django import template
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag
def galactic_thumb_url(target, size=120, fov=0.05):
    """
    Legacy helper: return only the thumbnail URL.
    """
    info = galactic_thumb_info(target, size=size, fov=fov)
    return info.get("url", "")


@register.simple_tag
def galactic_thumb_info(target, size=120, fov=0.035):
    """
    Return a dict with:
      - url:  sky cutout URL (JPG) around the target
      - fov_arcmin: FoV in arcmin as string (e.g. '2.1')

    No images are stored locally; the browser fetches them from the remote service.
    """
    ra = getattr(target, "ra", None)
    dec = getattr(target, "dec", None)

    if ra is None or dec is None:
        return {"url": "", "fov_arcmin": ""}

    try:
        size = int(size)
    except (TypeError, ValueError):
        size = 120

    try:
        fov = float(fov)
    except (TypeError, ValueError):
        fov = 0.035  # ~2.1 arcmin
    fov_arcmin = fov * 60.0

    base_url = "https://alasky.u-strasbg.fr/hips-image-services/hips2fits"
    params = {
        "hips": "CDS/P/DSS2/color",
        "width": size,
        "height": size,
        "fov": fov,
        "projection": "TAN",
        "coordsys": "icrs",
        "ra": ra,
        "dec": dec,
        "format": "jpg",
    }
    url = f"{base_url}?{urlencode(params)}"
    return {
        "url": url,
        "fov_arcmin": f"{fov_arcmin:.2f}".rstrip("0").rstrip("."),  # e.g. 2.1 or 2
    }

