from .base import *
from src import vault
from src.vault import credentials
DEBUG = False

ALLOWED_HOSTS = ["*"]
CORS_ORIGIN_ALLOW_ALL = False

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]


DATABASES = {
    "default": {
        "ENGINE": credentials['prod']['DB_ENGINE'],
        "NAME": credentials['prod']['DB_NAME'],
        "USER": credentials['prod']['DB_USER'],
        "PASSWORD": credentials['prod']['DB_PASSWORD'],
        "HOST": credentials['prod']['DB_HOST'],  # set in docker-compose.yml
        "PORT": credentials['prod']['DB_PORT'],  # default postgres port
    },
}

EMAIL = credentials['prod']["EMAIL"]
PASSWORD = credentials['prod']["PASSWORD"]

# AWS credentials

# PROD SECRET KEYS
S3_BUCKET = credentials['prod']['S3_BUCKET']
AWS_ACCESS_KEY_ID = credentials['prod']['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = credentials['prod']['AWS_SECRET_ACCESS_KEY']
REGION = credentials['prod']['REGION']
AWS_URL = "https://%s.s3.%s.amazonaws.com" % (S3_BUCKET, REGION)

# Frontend Urls
FRONTEND_BASE_URL = credentials['prod']['FRONTEND_BASE_URL']
ADMIN_FRONTEND_BASE_URL = credentials['prod']['ADMIN_FRONTEND_BASE_URL']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# TODO: More details on it.
if not DEBUG:
    SECURE_HSTS_SECONDS = 86400
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    INSTALLED_APPS.remove('debug_toolbar')
    MIDDLEWARE.remove("atomicloops.middleware.QueryCountMiddleware",)
    MIDDLEWARE.remove("debug_toolbar.middleware.DebugToolbarMiddleware")
