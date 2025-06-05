from .base import *
import os



DEBUG = False

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.users.middleware.RestrictBrowsableAPIMiddleware', 
]

SECRET_KEY = os.getenv('SECRET_KEY')

# Configuración HTTPS
ALLOWED_HOSTS = ['naia.uninorte.edu.co', '40.70.47.15']

# Configuración para proxy HTTPS (Nginx)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF para HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://naia.uninorte.edu.co',
    'https://40.70.47.15'
]

# CORS para HTTPS
CORS_ALLOWED_ORIGINS = [
    'https://naia.uninorte.edu.co',
    'https://40.70.47.15'
]
CORS_ALLOW_CREDENTIALS = True

# Configuraciones adicionales de seguridad
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('db_name'),
        'USER': os.getenv('db_user'),
        'PASSWORD': os.getenv('db_password'),
        'HOST': os.getenv('db_host'),   
        'PORT': '3306',     
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]
