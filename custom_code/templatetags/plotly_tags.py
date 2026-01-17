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
        values = [data_obj.metric_fink, data_obj.metric_alerce, data_obj.metric_antares, 
                  data_obj.metric_nsquare, data_obj.metric_phi]
    except:
        values = [0.1,0.2,0.3,0.4,0.5]


    categories = [
    "Metric Fink",
    "Metric ALeRCE",
    "Metric ANTARES",
    "Metric Nsquare",
    "Metric Planet Psi",
    ]

    values += values[:1]
    categories += categories[:1]

    fig = go.Figure()
    bogus_value = data_obj.metric_bogus
    fig.add_trace(
        go.Scatterpolar(
            r=[bogus_value] * len(categories),
            theta=categories,
            fill="toself",
            fillcolor="rgba(0, 255, 0, 0.3)",
            line=dict(color="green", dash="dash"),
            name="Bogus",
            hoverinfo="skip",
        )
    )

    fig.add_annotation(
        x=0.5,
        y=0.9,
        xref="paper", yref="paper",
        text=f"Bogus: {bogus_value}",
        showarrow=False,
        font=dict(color="green", size=17),
        bgcolor="white",
    )

    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name="Rescaled Probability",
        marker=dict(color="red"),
        )
    )

    fig.update_layout(
        template="plotly_dark",
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        title="Microlensing Radar Transformed probabilities",
    )

    figure = plot(fig, output_type='div', show_link=False)

    return {'figure': figure}
    
