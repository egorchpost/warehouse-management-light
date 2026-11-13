"""WSGI config for config project."""

from django.core.wsgi import get_wsgi_application

from config.settings.utils import check_django_settings_module_is_set

check_django_settings_module_is_set()

application = get_wsgi_application()
