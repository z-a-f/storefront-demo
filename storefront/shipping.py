"""Customer-visible shipping rules."""

FREE_SHIPPING_THRESHOLD_CENTS = 5_000
STANDARD_SHIPPING_FEE_CENTS = 1_500


def shipping_fee_cents(subtotal_cents: int, *, is_vip: bool = False) -> int:
    """Return the shipping fee for an order.

    VIP customers always receive free shipping. Other customers receive free
    shipping once their subtotal reaches the configured threshold.
    """
    return (
        0
        if is_vip or subtotal_cents >= FREE_SHIPPING_THRESHOLD_CENTS
        else STANDARD_SHIPPING_FEE_CENTS
    )
