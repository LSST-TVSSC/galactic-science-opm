from django import template
from django.core.exceptions import ObjectDoesNotExist
import plotly.graph_objects as go
from plotly.offline import plot
from custom_code.target_models import GalacticTarget
from custom_code.target_models import MicrolensingRadarData

register = template.Library()

@register.inclusion_tag('custom_code/radar_plot.html')
def render_radar_plot(name):
    try:
        data_obj =  MicrolensingRadarData.objects.filter(target=name).latest()
    except ObjectDoesNotExist:
        return None

    categories = ['Metric Fink', 'Metric ALeRCE', 'Metric ANTARES', 'Metric Nsquare', 'Metric Planet Phi']
    values = [data_obj.metric_fink, data_obj.metric_alerce, data_obj.metric_antares, 
              data_obj.metric_nsquare, data_obj.metric_phi]

    values += values[:1]
    categories += categories[:1]

    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False
    )

    return plot(fig, output_type='div', include_plotlyjs=False)

