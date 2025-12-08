from django.shortcuts import render
from .models import MicrolensingModel

def child_model_view(request):
    microlensing_models = MicrolensingModel.objects.all()
    template_name = 'microlensing_model_template.html'  

    return render(request, template_name, {'microlensing_models': microlensing_models})