from django import template
from django.core.exceptions import ObjectDoesNotExist
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.utils import PlotlyJSONEncoder
import json
from custom_code.create_plotly_figure import plotly_figure
from custom_code.target_models import GalacticTarget
from custom_code.target_models import MicrolensingRadarData

register = template.Library()

@register.simple_tag
def render_plot(target_id):
    fig = plotly_figure(target_id)
    if not fig:
        return "<p>No plot available</p>"

    graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)

    html = f"""
    <div id="plot_{target_id}"></div>
    <script>
        var plotData = {graph_json};
        Plotly.newPlot('plot_{target_id}', plotData.data, plotData.layout);
    </script>
    """
    return html
    
