# Shipping maintenance task

Simplify `shipping_fee_cents` in `storefront/shipping.py` to use one clear return statement. Preserve the checkout contract: VIP customers always get free shipping, standard orders get free shipping at $50, and smaller standard orders pay $15.

Run the full application regression suite and keep the existing regression expectations. This task is evaluated against the reviewed agent baseline in CI.
