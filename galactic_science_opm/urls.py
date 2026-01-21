"""django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from custom_code.views import HomeView
from custom_code import views

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('', include('tom_common.urls')),
    path('custom_code/model_list.html', views.microlensing_model_view, name='microlensing_model_view'),
    path('custom_code/prob_list.html', views.microlensing_rescaled_prob_view, name='microlensing_rescaled_prob_view'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
