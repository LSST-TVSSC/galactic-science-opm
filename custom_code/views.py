from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView
from custom_code.target_models import GalacticTarget

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, logout as auth_logout
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect

class HomeView(TemplateView):
    template_name = "tom_common/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Very simple first pass: just take the 5 most recent targets
        # (we know they at least have id and name).
        # This can be modifed with any selector function later.
        featured = (
            GalacticTarget.objects
            .order_by("-pk")[:5]
        )

        context["featured_targets"] = featured
        return context

@login_required
def account_delete(request):
    """
    Allow a logged-in user to delete their account.

    We anonymise personal fields and deactivate the user, while leaving
    science data in place (no longer personally identifiable).
    """
    if request.method == "POST":
        User = get_user_model()
        user = request.user

        with transaction.atomic():
            # Generate a unique anonymised username
            base_username = f"deleted_user_{user.pk}"
            new_username = base_username
            counter = 1

            while User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                new_username = f"{base_username}_{counter}"
                counter += 1

            user.username = new_username
            user.first_name = ""
            user.last_name = ""
            user.email = ""
            user.is_active = False

            # Remove from all groups
            user.groups.clear()

            user.save()

        # End the session
        auth_logout(request)
        messages.success(
            request,
            "Your account has been deleted and your personal data removed from the OPM."
        )
        return redirect("home")

    # GET: show confirmation page
    return render(request, "custom_code/account_delete.html")

