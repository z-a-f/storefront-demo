"""Catalog and checkout quotes. All prices are integer USD cents."""

import json
from pathlib import Path

from storefront.shipping import shipping_fee_cents

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def catalog() -> list[dict]:
    return json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))


def quote(items: list[dict], *, is_vip: bool = False) -> dict:
    if type(is_vip) is not bool:
        raise ValueError("is_vip must be true or false")
    if not isinstance(items, list) or not items or len(items) > 30:
        raise ValueError("Choose at least one item; at most 30 cart lines are allowed")
    products = {product["sku"]: product for product in catalog()}
    quantities = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each item needs a sku and quantity")
        sku, quantity = item.get("sku"), item.get("quantity")
        if not isinstance(sku, str) or sku not in products:
            raise ValueError("Unknown product SKU")
        if type(quantity) is not int or not 1 <= quantity <= 20:
            raise ValueError("Quantity must be a whole number from 1 to 20")
        quantities[sku] = quantities.get(sku, 0) + quantity
        if quantities[sku] > 20:
            raise ValueError("At most 20 pairs per product are allowed")
    lines = [
        {
            "sku": sku,
            "name": products[sku]["name"],
            "quantity": quantity,
            "price_cents": products[sku]["price_cents"],
            "line_total_cents": products[sku]["price_cents"] * quantity,
        }
        for sku, quantity in quantities.items()
    ]
    subtotal = sum(line["line_total_cents"] for line in lines)
    shipping = shipping_fee_cents(subtotal, is_vip=is_vip)
    return {
        "items": lines,
        "is_vip": is_vip,
        "subtotal_cents": subtotal,
        "shipping_cents": shipping,
        "total_cents": subtotal + shipping,
    }


def sample_orders() -> list[dict]:
    orders = json.loads((DATA_DIR / "orders.json").read_text(encoding="utf-8"))
    return [
        {**order, **quote(order["items"], is_vip=order["is_vip"])} for order in orders
    ]
