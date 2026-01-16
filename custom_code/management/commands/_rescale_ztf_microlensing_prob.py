import numpy as np
import pandas as pd
import os
import re
import math
import joblib
import warnings
import uncertainties as unc

def psi_planet_priority_peak(u0_pspl, u0_err, sigma_threshold = 1):
    """
    This function calculates the peak planet probabiltity for 
    microlensing events based on the planet probability psi
    as defined by Dominik et al. 2009. It subtracts 1 sigma of psi 
    to reflect poor fits as reported by the respective model
    """

    # Catch invalid input
    if np.isnan(u0_pspl) or np.isnan(u0_err):
        return 0.0
    u0 = unc.ufloat(u0_pspl,u0_err)
    usqr = u0**2
    pspl_deno = (usqr * (usqr + 4.))**0.5
    if pspl_deno < 1e-10:
        pspl_deno = 10000.
    psip = 4.0 / (pspl_deno) - 2.0 / (usqr + 2.0 + pspl_deno)

    if np.isnan(psip.nominal_value):
        psip = 0.0

    return psip.nominal_value -  sigma_threshold * psip.std_dev