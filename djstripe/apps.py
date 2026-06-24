"""
dj-stripe - Django + Stripe Made Easy
"""
import os

from django.apps import AppConfig

pyproject_toml_location = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
with open(pyproject_toml_location) as f:
    for line in f:
        if line.startswith("version"):
            __version__ = line.split("=")[1].strip().strip('"')
            break
    else:
        raise RuntimeError(f"Could not find version in {pyproject_toml_location}")


class DjstripeAppConfig(AppConfig):
    """
    An AppConfig for dj-stripe which loads system checks
    and event handlers once Django is ready.
    """

    name = "djstripe"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import stripe_sub5 as stripe

        from . import checks, event_handlers

        # Set app info
        # https://stripe.com/docs/building-plugins#setappinfo
        stripe.set_app_info(
            "djstripe",
            version=__version__,
            url="https://github.com/dj-stripe/dj-stripe",
        )
