import unittest
from unittest.mock import Mock

from src.models import CartItem, Order
from src.pricing import PricingService, PricingError
from src.checkout import CheckoutService, ChargeResult

class TestCheckoutService(unittest.TestCase):
	def setUp(self):
		self.payments = Mock()
		self.email = Mock()
		self.fraud = Mock()
		self.repo = Mock()
		
		self.checkout_service = CheckoutService(
			payments=self.payments,
			email=self.email,
			fraud=self.fraud,
			repo=self.repo,
		)
	
	def test_invalid_user(self):
		items = [CartItem("A", 1000, 1)]
		result = self.checkout_service.checkout("", items, "token", "CL")
		self.assertEqual(result, "INVALID_USER")

	def test_invalid_cart(self):
		items = [CartItem("A", 1000, 0)]
		result = self.checkout_service.checkout("1", items, "token", "CL")
		self.assertTrue(result.startswith("INVALID_CART:"))

	def test_rejected_fraud(self):
		self.fraud.score.return_value = 80
		items = [CartItem("A", 1000, 1)]
		result = self.checkout_service.checkout("1", items, "token", "CL")
		self.assertEqual(result, "REJECTED_FRAUD")
		self.payments.charge.assert_not_called()

	def test_payment_failed(self):
		self.fraud.score.return_value = 0
		self.payments.charge.return_value = ChargeResult(ok=False)
		items = [CartItem("A", 1000, 1)]
		result = self.checkout_service.checkout("1", items, "token", "CL")
		self.assertTrue(result.startswith("PAYMENT_FAILED:"))
		self.repo.save.assert_not_called()
		self.email.send_receipt.assert_not_called()

	def test_payment_successful(self):
		self.fraud.score.return_value = 0
		self.payments.charge.return_value = ChargeResult(ok=True, charge_id=1)
		items = [CartItem("A", 1000, 1)]
		result = self.checkout_service.checkout("1", items, "token", "CL")
		self.assertTrue(result.startswith("OK:"))
		self.repo.save.assert_called_once()
		self.email.send_receipt.assert_called_once()
