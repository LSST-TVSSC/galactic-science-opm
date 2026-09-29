import json

import plotly
from django import template
from tom_observations.templatetags.observation_extras import observation_plan

register = template.Library()


@register.inclusion_tag("tom_observations/partials/custom_observation_plan.html")
def custom_observation_plan(
    target, facility=None, length=2, interval=60, airmass_limit=None
):
    result = observation_plan(target, facility, length, interval, airmass_limit)
    fig_as_json = result["visibility_graph"]
    # generate a Figure from the json
    fig = plotly.io.from_json(json.dumps(fig_as_json))
    # set theme to dark mode
    fig.update_layout(template="plotly_dark")

    # generate graph for consumption again
    visibility_graph = plotly.offline.plot(fig, output_type="div", show_link=False)
    return {"visibility_graph": visibility_graph}
