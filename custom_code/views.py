from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView
from custom_code.target_models import GalacticTarget


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

