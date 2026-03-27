"""
sync_plans_from_stripe command.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Sync prices (and plans) from stripe_sub5."""

    help = "Sync prices (and plans) from stripe_sub5."

    def handle(self, *args, **options):
        call_command("djstripe_sync_models", "Price", "Plan")
