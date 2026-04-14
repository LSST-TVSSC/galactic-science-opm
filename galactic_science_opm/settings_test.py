from .settings import *

DEBUG = False

# add password hashing alternative once this is working

ALLOWED_HOSTS = ['frontend-proxy']

DATABASES["default"] = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.getenv('DB_NAME', 'galactic_science_opm'),
    'USER': os.getenv('DB_USER', 'opm'),
    'PASSWORD': os.getenv('DB_PASSWORD', 'opm'),
    'HOST': os.getenv('DB_HOST_TEST', '127.0.0.1'),
    'PORT': '5432',
}

