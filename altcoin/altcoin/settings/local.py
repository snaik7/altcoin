from .base import *


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
#SECRET_KEY = 's(00i4e7920#^01x^cx$d=x3fqbbl3hbo4+rasdsic+iu^wu#0'


#https://medium.com/@ayarshabeer/django-best-practice-settings-file-for-multiple-environments-6d71c6966ee2

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases



DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "altcoin",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

db_uri = 'postgresql://postgres:postgres@localhost:5432/altcoin'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
'''
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'santosh@tissatech.com'
EMAIL_HOST_PASSWORD = 'Mphasis7'
'''
EMAIL_HOST = '127.0.0.1'
EMAIL_PORT = 25

ACTIVEMQ_USER = 'admin'
ACTIVEMQ_PASSWORD = 'admin'
ACTIVEMQ_HOST = 'localhost'
ACTIVEMQ_PORT = 61613

RABBITMQ_USERNAME = 'guest'
RABBITMQ_PASSWORD = 'guest'
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 15672

PUBSUB = {
        'RABBITMQ_USERNAME': RABBITMQ_USERNAME,
        'RABBITMQ_PASSWORD': RABBITMQ_PASSWORD,
        'RABBITMQ_HOST': RABBITMQ_HOST,
        'RABBITMQ_PORT': RABBITMQ_PORT,
}

