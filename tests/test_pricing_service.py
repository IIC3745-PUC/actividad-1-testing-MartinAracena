import unittest
from unittest.mock import Mock

from src.models import CartItem, Order
from src.pricing import PricingService, PricingError

class TestPricingService(unittest.TestCase):
	def setUp(self):
		self.pricing_service = PricingService()
	
	def test_correct_subtotal(self):
		items = [
			CartItem("A", 1000, 2),
			CartItem("B", 500, 3),
		]
		self.assertEqual(self.pricing_service.subtotal_cents(items), 1000*2 + 500*3)
	
	def test_subtotal_invalid_qty(self):
		items = [CartItem("A", 1000, 0)]
		with self.assertRaises(PricingError):
			self.pricing_service.subtotal_cents(items)

	def test_subtotal_invalid_price(self):
		items = [CartItem("A", -10, 1)]
		with self.assertRaises(PricingError):
			self.pricing_service.subtotal_cents(items)

	def test_apply_no_coupon(self):
		self.assertEqual(self.pricing_service.apply_coupon(subtotal=1000, coupon_code=None), 1000)
		self.assertEqual(self.pricing_service.apply_coupon(subtotal=1000, coupon_code=""), 1000)
		self.assertEqual(self.pricing_service.apply_coupon(subtotal=1000, coupon_code="  "), 1000)
	
	def test_apply_coupon_save10(self):
		self.assertEqual(self.pricing_service.apply_coupon(subtotal=1000, coupon_code="SAVE10"), 1000*0.9)

	def test_apply_coupon_clp2000(self):
		self.assertEqual(self.pricing_service.apply_coupon(subtotal=10000, coupon_code="CLP2000"), 10000-2000)
	
	def test_apply_coupon_invalid(self):
		with self.assertRaises(PricingError):
			self.pricing_service.apply_coupon(1000, "INVALID")

	def test_tax_per_country(self):
		self.assertEqual(self.pricing_service.tax_cents(10000, "CL"), 1900)
		self.assertEqual(self.pricing_service.tax_cents(10000, "US"), 0)
		self.assertEqual(self.pricing_service.tax_cents(10000, "EU"), 2100)

	def test_tax_error(self):
		with self.assertRaises(PricingError):
			self.pricing_service.tax_cents(10000, "INVALID")

	def test_shipping_per_country(self):
		self.assertEqual(self.pricing_service.shipping_cents(20000, "CL"), 0)
		self.assertEqual(self.pricing_service.shipping_cents(10000, "CL"), 2500)
		self.assertEqual(self.pricing_service.shipping_cents(10000, "US"), 5000)
		self.assertEqual(self.pricing_service.shipping_cents(10000, "EU"), 5000)
		with self.assertRaises(PricingError):
			self.pricing_service.shipping_cents(1000, "INVALID")

	def test_total_after_taxes_and_shipping(self):
		items = [CartItem("A", 10000, 1)]
		total = self.pricing_service.total_cents(items, "CLP2000", "CL")
		self.assertEqual(total, 8000 + 8000*0.19 + 2500)
