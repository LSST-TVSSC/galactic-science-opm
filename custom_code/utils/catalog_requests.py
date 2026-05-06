from astroquery.vizier import Vizier
from astropy.coordinates import Angle

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

