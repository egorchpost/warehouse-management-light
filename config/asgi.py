"""ASGI config for config project."""

from django.core.asgi import get_asgi_application

from config.settings.utils import check_django_settings_module_is_set

check_django_settings_module_is_set()

application = get_asgi_application()
