from django.shortcuts import render
from .target_models import MicrolensingModel
from .target_models import Classification

def microlensing_model_view(request):
    microlensing_models = MicrolensingModel.objects.all()  # Get all MicrolensingModels
    return render(request, 'custom_code/model_list.html', {'microlensing_models': microlensing_models})
