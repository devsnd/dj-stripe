"""
dj-stripe Dispute model tests
"""
from copy import deepcopy
from unittest.mock import patch

import pytest
from django.test.testcases import TestCase

from djstripe.models import Charge, APIKey
from . import (
    FAKE_CHARGE_WITH_CONNECTED_ACCOUNT,
    FAKE_BALANCE_TRANSACTION_II,
    FAKE_EXPRESS_ACCOUNT,
    FAKE_TRANSFER,
    TransferDict,
    FAKE_PLATFORM_ACCOUNT,
)
from .settings import STRIPE_TEST_SECRET_KEY

pytestmark = pytest.mark.django_db


class TestConnect(TestCase):
    @patch(
        "stripe.BalanceTransaction.retrieve",
        return_value=deepcopy(FAKE_BALANCE_TRANSACTION_II),
        autospec=True,
    )
    @patch(
        "stripe.Account.retrieve",
        return_value=deepcopy(FAKE_EXPRESS_ACCOUNT),
        autospec=True,
    )
    @patch(
        "stripe.Transfer.retrieve",
        return_value=deepcopy(TransferDict(FAKE_TRANSFER)),
        autospec=True,
    )
    def test_resolve_account_for_charge(
        self,
        balance_transaction_retrieve_mock,
        account_retrieve_mock,
        transfer_retrieve_mock,
    ):
        # set the main account on the api key
        apikey_instance, _ = APIKey.objects.get_or_create_by_api_key(
            STRIPE_TEST_SECRET_KEY
        )
        apikey_instance.djstripe_owner_account = FAKE_PLATFORM_ACCOUNT.create()
        apikey_instance.save()
        # synchronize a charge that of a connected account
        charge = Charge.sync_from_stripe_data(FAKE_CHARGE_WITH_CONNECTED_ACCOUNT)
        self.assertEqual(charge.djstripe_owner_account.id, 'acct_1IuHosQveW0ONQsd')
