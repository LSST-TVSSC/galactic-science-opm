from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from tom_targets.base_models import BaseTarget

class GalacticTarget(BaseTarget):
    """
    Galactic Target model designed to allow for microlensing as well as other variability types

    Custom fields
    base_{ugrizy}_mag  float   Median magnitude at baseline in ugrizy passbands
    err_{ugrizy}_mag  float   Uncertainty in baseline magnitude in ugrizy passbands
    target_type string      Target category e.g. microlensing event, cataclysmic variable etc
    class_alerce    obj     Current-most-probable classification from the Alerce broker
    class_antares    obj     Current-most-probable classification from the ANTARES broker
    class_fink    obj     Current-most-probable classification from the Fink broker
    """

    base_u_mag = models.FloatField(default=0)
    err_u_mag = models.FloatField(default=0)
    base_g_mag = models.FloatField(default=0)
    err_g_mag = models.FloatField(default=0)
    base_r_mag = models.FloatField(default=0)
    err_r_mag = models.FloatField(default=0)
    base_i_mag = models.FloatField(default=0)
    err_i_mag = models.FloatField(default=0)
    base_z_mag = models.FloatField(default=0)
    err_z_mag = models.FloatField(default=0)
    base_y_mag = models.FloatField(default=0)
    err_y_mag = models.FloatField(default=0)
    target_type = models.CharField(max_length=50, default='Microlensing candidate')

    class Meta:
        verbose_name = "target"
        permissions = (
            ('view_target', 'View Target'),
            ('add_target', 'Add Target'),
            ('change_target', 'Change Target'),
            ('delete_target', 'Delete Target')
        )

    def get_target_names(self, qs):
        """Attributes the names associated with this target"""
        self.targetnames = []
        for name in qs:
            self.targetnames.append(name.name)

    def get_target_name_survey(self, survey):
        """
        Method to identify the name for the current Target from a specific survey.
        Returns None if the survey has not detected the Target and hence there would be no name.
        Input:
            survey  str     Identifier used in Target names to distinguish detections from that survey, e.g.
                            'Gaia' or 'OGLE'

        Returns
            survey_name str Name string from the survey or None
        """

        survey_name = None

        # Check the primary name for the survey identifier
        if survey in self.name:
            survey_name = self.name

        # If not, check the aliases for the survey identifier:
        else:
            for tn in self.aliases.all():
                if survey in tn.name:
                    survey_name = tn.name

class Classification(models.Model):
    """
    Class to capture timeseries information about classifications coming from different brokers

    source      Broker or archive where the classification originate
    class1      Current most-probable classification
    prob_class1 Probability of class1
    class2      Current most-probable classification
    prob_class2 Probability of class1
    class3      Current most-probable classification
    prob_class3 Probability of class1
    """

    target = models.ForeignKey(GalacticTarget, on_delete=models.CASCADE,null=True,blank=True, related_name="classification_parameters")
    source = models.CharField(max_length=50)
    class1 = models.CharField(max_length=50)
    prob_class1 = models.FloatField(default=0, null=True)
    class2 = models.CharField(max_length=50, null=True)
    prob_class2 = models.FloatField(default=0, null=True)
    class3 = models.CharField(max_length=50, null=True)
    prob_class3 = models.FloatField(default=0, null=True)
    prob_master_peak = models.FloatField(default=0, null=True)
    prob_master_current = models.FloatField(default=0, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        get_latest_by = 'updated_at'

    def __str__(self):
        s = f'{self.target}, {self.source}, {self.class1}, {self.prob_class1}'
        return s

class MicrolensingModel(models.Model):
    """Class providing the parameters of a microlensing model fit"""

    # Microlensing-specific fields
    target = models.ForeignKey(GalacticTarget, on_delete=models.CASCADE,null=True,blank=True, related_name="microlensing_parameters")
    t0 = models.FloatField(default=0)
    err_t0 = models.FloatField(default=0)
    u0 = models.FloatField(default=0)
    err_u0 = models.FloatField(default=0)
    tE = models.FloatField(default=0)
    err_tE = models.FloatField(default=0)
    piEN = models.FloatField(default=0)
    err_piEN = models.FloatField(default=0)
    piEE = models.FloatField(default=0)
    err_piEE = models.FloatField(default=0)
    rho = models.FloatField(default=0)
    err_rho = models.FloatField(default=0)
    s = models.FloatField(default=0)
    err_s = models.FloatField(default=0)
    q = models.FloatField(default=0)
    err_q = models.FloatField(default=0)
    alpha = models.FloatField(default=0)
    err_alpha = models.FloatField(default=0)
    source_mag = models.FloatField(default=0)
    err_source_mag = models.FloatField(default=0)
    blend_mag = models.FloatField(default=0)
    err_blend_mag = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        get_latest_by = 'updated_at'


class MicrolensingRadarData(models.Model):
    """
    Radar Model Data to keep the rescaled probabilities, can be averaged and 
    as the name suggests displayed in a plotly radar plot

    metric_alerce float   Rescaled probability from the Alerce broker filter
    metric_antares float Rescaled probability from the ANTARES broker
    metric_fink    obj   Rescaled probability from the Fink broker
    metric_planet float  Rescaled planet probability Fit and Phi function (Dominik et al.)
    metric_nsquare float Rescaled rank from Gaia Nsquare map
    """
    target = models.ForeignKey(GalacticTarget, on_delete=models.CASCADE,null=True,blank=True, related_name="rescaled_classification_radar_parameters")
    metric_fink = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    metric_alerce = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    metric_antares = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    metric_nsquare = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    metric_planet = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    average_master_probability = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    class Meta:
        get_latest_by = 'updated_at'

