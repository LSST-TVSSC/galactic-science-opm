from django.urls import path

from sed_plots import views

app_name = "sed_plots"

urlpatterns = [
    path(
        "targets/<int:target_id>/fetch-vizier-sed/",
        views.fetch_vizier_sed,
        name="fetch_vizier_sed",
    ),
]
