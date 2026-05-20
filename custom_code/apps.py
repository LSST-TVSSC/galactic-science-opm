import joblib
from pathlib import Path
from sklearn.preprocessing import QuantileTransformer
from django.apps import AppConfig
import healpy as hp


class CustomCodeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'custom_code'

    def ready(self):
        # prepare probability scalers
        if not hasattr(self, 'models_loaded'):
            base_path = Path(__file__).resolve().parent / "auxiliary_data"

            self.model_qt_psi = joblib.load(base_path / "quantile_transformer_psi_peak.joblib")
            self.model_qt_fink = joblib.load(base_path / "quantile_transformer_fink.joblib")
            self.model_qt_alerce = joblib.load(base_path / "quantile_transformer_alerce.joblib")
            self.model_qt_alerce_atat = joblib.load(base_path / "quantile_transformer_alerce_atat.joblib")
            self.nsquare_map = hp.read_map(base_path / "gaia_nsquare_for_OPM_uniform_transform.fits.gz")
            self.nvisits_10yrs_map = hp.read_map(base_path / "filtered_survey_map_visits.fits.gz")
            self.nside = hp.get_nside(self.nsquare_map)

            self.models_loaded = True