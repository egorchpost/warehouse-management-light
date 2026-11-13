import os

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured


def check_django_settings_module_is_set():
    load_dotenv()

    module = os.getenv("DJANGO_SETTINGS_MODULE")

    if not module:
        raise ImproperlyConfigured(
            "DJANGO_SETTINGS_MODULE environment variable not set."
        )

    if module not in ("config.settings.dev", "config.settings.prod"):
        raise ImproperlyConfigured(
            "DJANGO_SETTINGS_MODULE environment variable is wrong."
        )
