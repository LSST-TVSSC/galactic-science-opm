from django.shortcuts import render
from custom_code.target_models import GalacticTarget
from custom_code.target_models import MicrolensingModel
from custom_code.target_models import Classification
from django.views.generic import TemplateView

def microlensing_model_view(request):
    microlensing_models = MicrolensingModel.objects.all()  # Get all MicrolensingModels
    return render(request, 'custom_code/model_list.html', {'microlensing_models': microlensing_models})

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

