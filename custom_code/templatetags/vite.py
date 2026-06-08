import json
import os
import pathlib
import random
from django.conf import settings
from django import template
register = template.Library()

prefix = ""
if settings.DEBUG:
    prefix = "custom_code"

MANIFEST_PATH = pathlib.Path(os.path.join(
    settings.BASE_DIR,prefix,"static/custom_code/dist/vite-manifest.json"
))

_manifest_cache = None
_manifest_mtime = None

# mkistner: I'll have to check if we need this. During development the old versions
# kept being reused, so this had to be introduced.
def get_manifest():
    global _manifest_cache, _manifest_mtime

    if not MANIFEST_PATH.exists():
        return {}

    mtime = MANIFEST_PATH.stat().st_mtime

    # reload if file changed
    if _manifest_cache is None or mtime != _manifest_mtime:
        with open(MANIFEST_PATH, "r") as f:
            _manifest_cache = json.load(f)
        _manifest_mtime = mtime

    return _manifest_cache

@register.simple_tag
def vite_asset(entry):
    manifest = get_manifest()
    return "/static/custom_code/dist/" + manifest[entry]["file"]