"""Checkout contracts for mock orders."""

import unittest

from storefront.orders import catalog, quote, sample_orders


class OrderTests(unittest.TestCase):
    def test_vip_checkout_totals_above_threshold(self):
        order = quote([{"sku": "sock-cloud", "quantity": 5}], is_vip=True)
        self.assertEqual(order["subtotal_cents"], 6000)
        self.assertEqual(order["shipping_cents"], 0)
        self.assertEqual(order["total_cents"], 6000)

    def test_standard_checkout_and_threshold(self):
        self.assertEqual(
            quote([{"sku": "sock-cloud", "quantity": 1}])["total_cents"], 2700
        )
        self.assertEqual(
            quote([{"sku": "sock-cloud", "quantity": 5}])["shipping_cents"], 0
        )

    def test_duplicate_lines_are_aggregated(self):
        order = quote(
            [{"sku": "sock-cloud", "quantity": 2}, {"sku": "sock-cloud", "quantity": 1}]
        )
        self.assertEqual(len(order["items"]), 1)
        self.assertEqual(order["items"][0]["quantity"], 3)

    def test_invalid_cart_is_rejected(self):
        for items in (
            [],
            [{"sku": "missing", "quantity": 1}],
            [{"sku": "sock-cloud", "quantity": 0}],
            [{"sku": "sock-cloud", "quantity": True}],
            [{"sku": "sock-cloud", "quantity": 21}],
            [{"sku": "sock-cloud", "quantity": 1.5}],
        ):
            with self.subTest(items=items), self.assertRaises(ValueError):
                quote(items)
        with self.assertRaises(ValueError):
            quote([{"sku": "sock-cloud", "quantity": 1}], is_vip="false")

    def test_samples_use_the_same_checkout_calculation(self):
        products = catalog()
        orders = sample_orders()
        self.assertEqual(len(products), 3)
        self.assertEqual(len(orders), 4)
        vip = next(order for order in orders if order["id"] == "SF-1001")
        self.assertEqual(vip["subtotal_cents"], 1200)
        self.assertEqual(vip["customer"], "Test Customer 01")
        for order in orders:
            self.assertEqual(
                order["total_cents"], order["subtotal_cents"] + order["shipping_cents"]
            )
