import json
import joblib
from pathlib import Path
from django.apps import AppConfig
import healpy as hp


class CustomCodeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "custom_code"

    def ready(self):
        # prepare probability scalers
        if not hasattr(self, "models_loaded"):
            base_path = Path(__file__).resolve().parent / "auxiliary_data"

            self.model_qt_psi = joblib.load(
                base_path / "quantile_transformer_psi_peak.joblib"
            )
            self.model_qt_fink = joblib.load(
                base_path / "quantile_transformer_fink.joblib"
            )
            self.model_qt_alerce = joblib.load(
                base_path / "quantile_transformer_alerce.joblib"
            )
            self.model_qt_alerce_atat = joblib.load(
                base_path / "quantile_transformer_alerce_atat.joblib"
            )
            self.nsquare_map = hp.read_map(
                base_path / "gaia_nsquare_for_OPM_uniform_transform.fits.gz"
            )
            self.nvisits_10yrs_map = hp.read_map(
                base_path / "filtered_survey_map_visits.fits.gz"
            )
            self.nside = hp.get_nside(self.nsquare_map)

            self.models_loaded = True

        # mkistner: Many of the plots by tomtoolkit use plotly.offline and return
        # the full plotly.js. With multiple charts, it gets included multiple times
        # and plotly is not small.
        # This monkeypatches plotly offline to NOT return plotly, so we can serve
        # it ourselves.
        # Further, this returns only the json from the backend to support loading
        # the script and plot only when it is visible.
        import plotly.offline as offline

        _original_plot = offline.plot

        def patched_plot(fig, *args, **kwargs):

            # mkistner: why the back and forth? because the data sometimes
            # contains fields that are not serializable with python's
            # json_script. This fixes that.
            data_as_json = fig.to_json()
            data = json.loads(data_as_json)
            return data

        offline.plot = patched_plot

    def target_detail_tabs(self):
        return [
            {
                "partial": "custom_code/tabs/photometry.html",
                "context": "custom_code.tabs.context.dummy",
                "label": "Photometry",
            },
            {
                "partial": "custom_code/tabs/imaging.html",
                "context": "custom_code.tabs.context.dummy",
                "label": "Imaging",
            },
            {
                "partial": "custom_code/tabs/spectroscopy.html",
                "context": "custom_code.tabs.context.dummy",
                "label": "Spectroscopy",
            },
            {
                "partial": "custom_code/tabs/classifications.html",
                "context": "custom_code.tabs.context.dummy",
                "label": "Classifications",
            },
            {
                "partial": "custom_code/tabs/analysis.html",
                "context": "custom_code.tabs.context.dummy",
                "label": "Analysis",
            },
            {
                "partial": "custom_code/tabs/observe.html",
                "context": "custom_code.tabs.context.dummy",
                "label": "Exchange",
            }

        ]
