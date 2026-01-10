from django import template
import plotly.graph_objects as go
from plotly.offline import plot

register = template.Library()

@register.simple_tag
def render_radar_plot(data_obj):
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

