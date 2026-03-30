"""
dj-stripe - Django + Stripe Made Easy
"""
import pkg_resources
from django.apps import AppConfig

__version__ = pkg_resources.get_distribution("djstripe").version


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
