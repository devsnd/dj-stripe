# Generated by Django 3.2.19 on 2023-11-13 16:07

from django.db import migrations
import djstripe.fields


class Migration(migrations.Migration):

    dependencies = [
        ('djstripe', '0012_balancetransaction_included_in_payout'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='cash_balance',
            field=djstripe.fields.JSONField(blank=True, null=True),
        ),
    ]
