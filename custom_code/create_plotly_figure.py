from custom_code.target_models import GalacticTarget
from custom_code.target_models import MicrolensingModel
from custom_code.target_models import Classification
from custom_code.target_models import MicrolensingRadarData
import plotly.graph_objects as go
from plotly.offline import plot

def plotly_figure(target_id):
    try:
        data_obj = MicrolensingRadarData.objects.filter(target_id=target_id).latest()
        values = [data_obj.metric_fink, data_obj.metric_alerce, data_obj.metric_antares, 
                  data_obj.metric_nsquare, data_obj.metric_planet]
        bogus_value = data_obj.metric_bogus
    except:
        values = [0.0,0.0,0.0,0.0,0.0]
        bogus_value = 0.

    categories = [
    "Metric Fink",
    "Metric ALeRCE",
    "Metric ANTARES",
    "Metric N&sup2",
    "Metric &#968; Peak",
    ]
    #connect first and last entry
    values += values[:1]
    categories += categories[:1]

    fig = go.Figure()
    #treat stamp bogus metric as envelope

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

    return figure
