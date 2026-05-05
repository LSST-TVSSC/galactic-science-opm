import os

VALID_USER_CREDENTIALS = ("max", "1234!!!!")
VALID_ADMIN_CREDENTIALS = ("admin", "1234")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

TOP_TARGETS = (
    {
        "name": "ZTF26aarbgfh",
        "coordinates": (274.577805040264, 2.056956216712028),
        "pk": 3,
    },
    {
        "name": "ZTF26aaivmks",
        "coordinates": (283.1755543793785, 0.4623901598870619),
        "pk": 4,
    },
    {
        "name": "ZTF26aajaofr",
        "coordinates": (274.50615820669293, -3.998751150664676),
        "pk": 6,
    },
)

TEST_TARGETS = (
    {"name": "ZTF26aaousvi", "pk": 40, "type": "SIDEREAL", "obs": 0, "saved": 0},
    {"name": "ZTF26aanhmik", "pk": 22, "type": "SIDEREAL", "obs": 0, "saved": 0},
)

BROKER_LINKS = (
    {
        "name": "ANTARES",
        "title": "Open ANTARES for {}",
        "href": "https://antares.noirlab.edu/loci/lookup/{}",
    },
    {
        "name": "ALeRCE",
        "title": "Open ALeRCE for {}",
        "href": "https://alerce.online/object/{}",
    },
    {
        "name": "Fink",
        "title": "Open Fink for {}",
        "href": "https://ztf.fink-portal.org/{}",
    },
)

REGISTERABLE_USER = {
    "username": "dude3",
    "first_name": "dude",
    "last_name": "duderson",
    "email": "dude@example.com",
    "password": "foo1234%",
    "password_confirm": "foo1234%",
    "affiliation": "dev"
}
