"""
dj-stripe CustomerCashBalanceTransaction model tests
"""
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

from djstripe.models import CustomerCashBalanceTransaction, Customer

from . import (
    FAKE_CUSTOMER,
    FAKE_PLATFORM_ACCOUNT,
)

pytestmark = pytest.mark.django_db


FAKE_CASH_BALANCE_TRANSACTION_FUNDED = {
    "id": "ccsbtxn_1ABC123DEF456GHI",
    "object": "customer_cash_balance_transaction",
    "created": 1700000000,
    "currency": "eur",
    "customer": "cus_6lsBvm5rJ0zyHc",
    "ending_balance": 10000,
    "funded": {
        "bank_transfer": {
            "eu_bank_transfer": {
                "bic": "TESTBIC",
                "iban_last4": "1234",
                "sender_name": "Test Sender",
            },
            "reference": "TEST-REF-123",
            "type": "eu_bank_transfer",
        }
    },
    "livemode": False,
    "net_amount": 10000,
    "type": "funded",
}

FAKE_CASH_BALANCE_TRANSACTION_FUNDED_EU_BANK_TRANSFER = {
    "id": "ccsbtxn_1TPeTjGBYoIVGZBUkK35xOpE",
    "object": "customer_cash_balance_transaction",
    "created": 1777016927,
    "currency": "eur",
    "customer": "cus_6lsBvm5rJ0zyHc",
    "customer_account": None,
    "ending_balance": 6900,
    "funded": {
        "bank_transfer": {
            "eu_bank_transfer": {
                "bic": "MARKDEF1760",
                "iban_last4": "1601",
                "sender_name": "Bundesagentur fur Arbeit-Service-Haus",
            },
            "reference": "TF-FS-xxxxxxxx-8 JULIA Bxxxx 124xxxxxxx24/27xxxxxxxx035",
            "type": "eu_bank_transfer",
        }
    },
    "livemode": True,
    "net_amount": 6900,
    "type": "funded",
}

FAKE_CASH_BALANCE_TRANSACTION_APPLIED = {
    "id": "ccsbtxn_2ABC123DEF456GHI",
    "object": "customer_cash_balance_transaction",
    "applied_to_payment": {
        "payment_intent": "pi_fake_nonexistent",
    },
    "created": 1700001000,
    "currency": "eur",
    "customer": "cus_6lsBvm5rJ0zyHc",
    "ending_balance": 3100,
    "funded": None,
    "livemode": False,
    "net_amount": -6900,
    "type": "applied_to_payment",
}


class TestCustomerCashBalanceTransactionSyncForCustomer(TestCase):
    def setUp(self):
        # Create a Stripe Platform Account
        self.account = FAKE_PLATFORM_ACCOUNT.create()

        self.user = get_user_model().objects.create_user(
            username="testuser", email="testuser@example.com"
        )
        self.customer = FAKE_CUSTOMER.create_for_user(self.user)

    @patch("djstripe.models.core.requests.get")
    def test_sync_for_customer_with_funded_transaction(self, mock_requests_get):
        """Test that sync_for_customer correctly syncs a funded cash balance transaction."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [FAKE_CASH_BALANCE_TRANSACTION_FUNDED],
            "has_more": False,
            "url": f"/v1/customers/{self.customer.id}/cash_balance_transactions",
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        # Call sync_for_customer
        instances = CustomerCashBalanceTransaction.sync_for_customer(self.customer)

        # Verify requests.get was called correctly
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        assert self.customer.id in call_args[0][0]

        # Verify the transaction was synced to the database
        assert len(instances) == 1
        instance = instances[0]
        assert instance.id == FAKE_CASH_BALANCE_TRANSACTION_FUNDED["id"]
        assert instance.currency == "eur"
        assert instance.ending_balance == 10000
        assert instance.net_amount == 10000
        assert instance.type == "funded"
        assert instance.funded == FAKE_CASH_BALANCE_TRANSACTION_FUNDED["funded"]
        assert instance.customer == self.customer
        assert instance.livemode is False

        # Verify it's persisted in the database
        db_instance = CustomerCashBalanceTransaction.objects.get(
            id=FAKE_CASH_BALANCE_TRANSACTION_FUNDED["id"]
        )
        assert db_instance.currency == "eur"
        assert db_instance.ending_balance == 10000

    @patch("djstripe.models.core.requests.get")
    def test_sync_for_customer_with_eu_bank_transfer_funded(self, mock_requests_get):
        """Test that sync_for_customer correctly syncs a funded transaction with EU bank transfer details."""
        # Mock the API response with realistic EU bank transfer data
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [FAKE_CASH_BALANCE_TRANSACTION_FUNDED_EU_BANK_TRANSFER],
            "has_more": False,
            "url": f"/v1/customers/{self.customer.id}/cash_balance_transactions",
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        # Call sync_for_customer
        instances = CustomerCashBalanceTransaction.sync_for_customer(self.customer)

        # Verify the transaction was synced
        assert len(instances) == 1
        instance = instances[0]
        assert instance.id == "ccsbtxn_1TPeTjGBYoIVGZBUkK35xOpE"
        assert instance.currency == "eur"
        assert instance.ending_balance == 6900
        assert instance.net_amount == 6900
        assert instance.type == "funded"
        assert instance.livemode is True

        # Verify the funded field contains the full EU bank transfer details
        assert instance.funded is not None
        assert instance.funded["bank_transfer"]["type"] == "eu_bank_transfer"
        assert instance.funded["bank_transfer"]["eu_bank_transfer"]["bic"] == "MARKDEF1760"
        assert instance.funded["bank_transfer"]["eu_bank_transfer"]["iban_last4"] == "1601"
        assert instance.funded["bank_transfer"]["eu_bank_transfer"]["sender_name"] == "Bundesagentur fur Arbeit-Service-Haus"
        assert instance.funded["bank_transfer"]["reference"] == "TF-FS-xxxxxxxx-8 JULIA Bxxxx 124xxxxxxx24/27xxxxxxxx035"

        # Verify it's correctly persisted in the database
        db_instance = CustomerCashBalanceTransaction.objects.get(
            id="ccsbtxn_1TPeTjGBYoIVGZBUkK35xOpE"
        )
        assert db_instance.funded["bank_transfer"]["eu_bank_transfer"]["bic"] == "MARKDEF1760"

    @patch("djstripe.models.core.requests.get")
    def test_sync_for_customer_with_multiple_transactions(self, mock_requests_get):
        """Test that sync_for_customer correctly syncs multiple cash balance transactions."""
        # Mock the API response with multiple transactions
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [
                FAKE_CASH_BALANCE_TRANSACTION_FUNDED,
                FAKE_CASH_BALANCE_TRANSACTION_APPLIED,
            ],
            "has_more": False,
            "url": f"/v1/customers/{self.customer.id}/cash_balance_transactions",
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        # Call sync_for_customer
        instances = CustomerCashBalanceTransaction.sync_for_customer(self.customer)

        # Verify both transactions were synced
        assert len(instances) == 2

        # Verify database contains both transactions
        assert CustomerCashBalanceTransaction.objects.count() == 2

        # Verify the funded transaction
        funded_instance = CustomerCashBalanceTransaction.objects.get(
            id=FAKE_CASH_BALANCE_TRANSACTION_FUNDED["id"]
        )
        assert funded_instance.type == "funded"
        assert funded_instance.net_amount == 10000

        # Verify the applied_to_payment transaction
        applied_instance = CustomerCashBalanceTransaction.objects.get(
            id=FAKE_CASH_BALANCE_TRANSACTION_APPLIED["id"]
        )
        assert applied_instance.type == "applied_to_payment"
        assert applied_instance.net_amount == -6900
        # PaymentIntent doesn't exist, so FK should be None (with warning logged)
        assert applied_instance.applied_to_payment_payment_intent is None

    @patch("djstripe.models.core.requests.get")
    def test_sync_for_customer_with_empty_response(self, mock_requests_get):
        """Test that sync_for_customer handles empty responses correctly."""
        # Mock an empty API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [],
            "has_more": False,
            "url": f"/v1/customers/{self.customer.id}/cash_balance_transactions",
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        # Call sync_for_customer
        instances = CustomerCashBalanceTransaction.sync_for_customer(self.customer)

        # Verify no instances returned
        assert len(instances) == 0
        assert CustomerCashBalanceTransaction.objects.count() == 0

    @patch("djstripe.models.core.requests.get")
    def test_sync_for_customer_with_customer_id_string(self, mock_requests_get):
        """Test that sync_for_customer works with a customer ID string."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [FAKE_CASH_BALANCE_TRANSACTION_FUNDED],
            "has_more": False,
            "url": f"/v1/customers/{self.customer.id}/cash_balance_transactions",
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        # Call sync_for_customer with a customer ID string
        instances = CustomerCashBalanceTransaction.sync_for_customer(self.customer.id)

        # Verify the transaction was synced
        assert len(instances) == 1
        assert instances[0].id == FAKE_CASH_BALANCE_TRANSACTION_FUNDED["id"]

    @patch("djstripe.models.core.requests.get")
    def test_sync_for_customer_updates_existing(self, mock_requests_get):
        """Test that sync_for_customer updates existing transactions."""
        # First sync
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [FAKE_CASH_BALANCE_TRANSACTION_FUNDED],
            "has_more": False,
            "url": f"/v1/customers/{self.customer.id}/cash_balance_transactions",
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        CustomerCashBalanceTransaction.sync_for_customer(self.customer)

        # Verify initial state
        instance = CustomerCashBalanceTransaction.objects.get(
            id=FAKE_CASH_BALANCE_TRANSACTION_FUNDED["id"]
        )
        assert instance.ending_balance == 10000

        # Second sync with updated data
        updated_transaction = deepcopy(FAKE_CASH_BALANCE_TRANSACTION_FUNDED)
        updated_transaction["ending_balance"] = 15000

        mock_response.json.return_value = {
            "object": "list",
            "data": [updated_transaction],
            "has_more": False,
            "url": f"/v1/customers/{self.customer.id}/cash_balance_transactions",
        }

        CustomerCashBalanceTransaction.sync_for_customer(self.customer)

        # Verify the update
        instance.refresh_from_db()
        assert instance.ending_balance == 15000

        # Verify still only one record
        assert CustomerCashBalanceTransaction.objects.count() == 1


class TestCustomerCashBalanceTransactionStr(TestCase):
    def setUp(self):
        self.account = FAKE_PLATFORM_ACCOUNT.create()
        self.user = get_user_model().objects.create_user(
            username="testuser", email="testuser@example.com"
        )
        self.customer = FAKE_CUSTOMER.create_for_user(self.user)

    @patch("djstripe.models.core.requests.get")
    def test___str__(self, mock_requests_get):
        """Test the string representation of CustomerCashBalanceTransaction."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [FAKE_CASH_BALANCE_TRANSACTION_FUNDED],
            "has_more": False,
            "url": f"/v1/customers/{self.customer.id}/cash_balance_transactions",
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        instances = CustomerCashBalanceTransaction.sync_for_customer(self.customer)
        instance = instances[0]

        # The __str__ method formats as: "{amount} ({type})"
        assert str(instance) == "€100.00 EUR (funded)"
