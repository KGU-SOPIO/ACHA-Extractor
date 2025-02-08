import os

from django.core.wsgi import get_wsgi_application
from django.urls import get_resolver
from Extractor.settings import ROOT_URLCONF

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Extractor.settings')

application = get_wsgi_application()

# URL Pre Load
get_resolver(ROOT_URLCONF).url_patterns