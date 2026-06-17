from django.conf import settings

def version_info(_request):
    """
    Provides the git commit hash (if provided via env) to use in a template.
    """
    return {
        "git_commit": settings.GIT_COMMIT,
    }