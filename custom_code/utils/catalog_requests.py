from astroquery.vizier import Vizier
from astropy.coordinates import Angle
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord
from io import StringIO, BytesIO
from urllib.parse import urlencode
import pandas as pd
import requests
from astropy.table import Table

# Where to find the VIZIER API
VIZIER_SED_API_URL = "https://vizier.cds.unistra.fr/viz-bin/sed"
VIZIER_SED_VIEWER_URL = "https://vizier.cds.unistra.fr/vizier/sed/"

NOT_IN_ANY_CATALOG = "None, queried"

def get_glade_plus_count(coords):
    """
    Queries GLADE+ galaxy catalog VII/281 for given skzycoord
    Returns the number of rows in the result table, 
    or -1.
    """
    radius = Angle(1.5 / 60. / 60., "deg")
    try:
        result = Vizier.query_region(coords, radius=radius, catalog='VII/281', cache=False)
        if not result or len(result) == 0:
            return 0            
        return len(result[0])
    except:
        return -1


def get_var_star_variability_analysis(ra , dec, radius_arcsec=3):
    """
    Queries the Vizier catalog for variable stars within a given regions
    as detailed as possible
    Args:
        ra (float): Right Ascension in degrees.
        dec (float): Declination in degrees.
        radius_arcsec (float): Search radius in arcseconds.

    Returns:
        str: Summary of found variability classifications.
    """
    
    try:
        VIZIER = Vizier(ucd="src.var", columns=["*"])
        VIZIER.ROW_LIMIT = -1 
    except Exception as e:
        print(f"Error initializing Vizier: {e}")
        VIZIER = None
        
    if VIZIER is None:
        return "No Vizier connection."

    coords = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs')
    radius = radius_arcsec * u.arcsec

    try:
        results = VIZIER.query_region(coords, radius=radius)
    except Exception as e:
        return f"Error Vizier query: {e}"

    if not results:
        return NOT_IN_ANY_CATALOG

    result_string=""
    for catalog_name in results.keys():
        table = results[catalog_name]
        var_col = None
        for col in table.colnames:
             if col.lower() in [
                "vartype",
                "type",
                "class",
                "var_type",
                "best_class_name",
                "vari_type",
            ]:
                var_col = col
                break
        if var_col and len(table) > 0:
            var_type = str(table[var_col][0])
            if not var_type in result_string:
                if result_string == "":
                    result_string = var_type
                else:
                    result_string = f"{result_string},{var_type}"
        else:
            pass
    return result_string


def get_vizier_sed_url(ra_deg, dec_deg, radius_arcsec=2.0):
    """
    Builds the public CDS VizieR SED viewer URL for a sky position.

    The viewer is useful as a robust fallback when the API call times out,
    returns no rows, or returns a format that cannot be parsed locally.
    """
    if ra_deg is None or dec_deg is None:
        return VIZIER_SED_VIEWER_URL

    params = {
        "-c": f"{float(ra_deg):.8f},{float(dec_deg):.8f}",
        "-c.rs": f"{float(radius_arcsec):.3f}",
    }
    return f"{VIZIER_SED_VIEWER_URL}?{urlencode(params)}"


def query_vizier_sed(ra_deg, dec_deg, radius_arcsec=2.0, timeout=5.0):
    """
    Query the CDS VizieR SED API around a sky position.

    Returns
    -------
    tuple
        (table, error_message). On success, table is an Astropy Table
        and error_message is None. On failure, table is None and
        error_message is a human-readable reason.
    """
    if ra_deg is None or dec_deg is None:
        return None, "No sky coordinates are available for this target."

    params = {
        "-c": f"{float(ra_deg):.8f},{float(dec_deg):.8f}",
        "-c.rs": f"{float(radius_arcsec):.3f}",
        "-out.form": "VOTable",
    }

    try:
        response = requests.get(VIZIER_SED_API_URL, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return None, "The VizieR SED query timed out."
    except requests.exceptions.RequestException as exc:
        return None, f"The VizieR SED query failed: {exc}"

    if not response.content or not response.content.strip():
        return None, "The VizieR SED query returned an empty response."

    try:
        sed_table = Table.read(BytesIO(response.content), format="votable")
    except Exception as exc:
        return None, f"The VizieR SED response could not be parsed: {exc}"

    if len(sed_table) == 0:
        return None, "No VizieR SED points were found near this target."

    required_columns = {"sed_freq", "sed_flux"}
    missing_columns = required_columns.difference(sed_table.colnames)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        return None, f"The VizieR SED response is missing required column(s): {missing}."

    return sed_table, None


def query_ztf_lightcurve(ra_deg, dec_deg, radius_arcsec, start_mjd=58500.0, passband="r"):
    """
    This function generates a pandas df formatted ZTF lightcurve using requests
    based on RA and Dec in degrees and a search radius in arcseconds.
    Optionally the start_mjd and passband can be given.

    The output contains the concatenated timeseries ZTF data as pandas dataframe.

    parameters:
    ra_deg (float): right ascension in degrees.
    dec_deg (float): declination in degrees.
    radius (float): query radius in arcseconds.

    optional parameters:
    start_mjd (float): start mjd in days.
    passband (str): ZTF passband, default r.

    returns:
    pandas dataframe of the lightcurve
    """
    if ra_deg >= 0.0:
        ra_str = " {0:.4f}".format(ra_deg)
    else:
        ra_str = " {0:.4f}".format(ra_deg)
    if dec_deg >= 0.0:
        dec_str = " {0:.4f}".format(dec_deg)
    else:
        dec_str = " {0:.4f}".format(dec_deg)
    radius_str = " {0:.4f}".format(radius_arcsec / 3600.0)
    mjd_now_str = "{:.1f}".format(Time.now().mjd)
    circle_position_string = "{}{}{}".format(ra_str, dec_str, radius_str)
    start_mjd_str = "{0:.1f}".format(start_mjd)
    try:
        pandas_df_lightcurve = pd.read_csv(
            StringIO(
                requests.get(
                    "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE{}&BANDNAME={}&NOBS_MIN=3&TIME={}+{}&BAD_CATFLAGS_MASK=32768&FORMAT=csv".format(
                        circle_position_string, passband, start_mjd_str, mjd_now_str
                    )
                ).text
            )
        )
    except Exception as e:
        print(f"Unexpected exception {e}")
    return pandas_df_lightcurve
