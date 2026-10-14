# Storefront

**Agent Controlled Storefront: Best Socks for AI**

Storefront is a local sock shop with a product catalog, a shopping bag, checkout quotes, and a fulfillment view of mock orders. The catalog and order records are checked into `data/`. All customers and orders are fictional; checkout calculates a quote without collecting payment or submitting an order.

## Run locally

Requires Git, uv, and Python 3.12 or 3.13.

```bash
uv sync --locked
uv run --frozen python -m storefront.server
```

Open **http://127.0.0.1:8000**. Add a pair to the bag, switch VIP membership on or off, and review the checkout quote. Select **Orders** to inspect the sample fulfillment queue. Stop the server with Ctrl+C. Restart it after changing Python code; refresh the browser after changing catalog or order fixtures. The bag is kept in browser memory and resets on refresh.

## Checkout rules

Prices are in USD, stored as integer cents. VIP customers always receive free shipping. Standard orders qualify for free shipping at a $50 subtotal; smaller orders pay $15. Quantities must be whole numbers from 1 to 20 per product. There are no taxes, discounts, inventory reservations, or payment integrations in this mock app.

Order `SF-1001` is a VIP customer buying one $12 Cloud Crew pair. Its shipping is $0 and its total is $12. The same bag for a standard customer costs $27. Use these cases when reviewing shipping changes.

## Project layout

- `storefront/shipping.py`: customer shipping rules.
- `storefront/orders.py`: catalog access and checkout calculations.
- `storefront/server.py`: local HTTP server and quote API.
- `storefront/static/`: storefront UI.
- `data/catalog.json`, `data/orders.json`: mock products and orders.
- `tests/`: checkout regressions and coding-agent behavior tests.
- `AGENTS.md`, `CLAUDE.md`: coding-agent responsibilities.
- `task.md`: the shipping maintenance task.
- `.maida/`: reviewed agent baseline and policy.
- `scenarios/`: manual development exercises and PR steps.

## Tests and code quality

```bash
uv run --frozen python -m unittest discover -s tests -p 'test_*.py' -q
uv run --frozen python -m pytest -q
uv run --frozen ruff check .
uv run --frozen ruff format --check .
```

The unittest command checks application regressions and the checked-in policy contract. Pytest additionally exercises the coding agent and isolated behavioral gate. Tests use local fixtures, without model-provider calls or external services.

## Coding-agent workflow

The shipping maintenance worker reads the repository instructions and performs the task in `task.md`. `coding_agent.py` is an offline worker with deterministic instruction matching; it executes real file edits and tests, without calling a live model. Running the worker directly edits your checkout. The CI runner evaluates it in fresh temporary copies and leaves your working files unchanged.

```bash
uv run --frozen python github_gate.py
```

This evaluates the current instructions against the reviewed baseline. An explicit PASS exits successfully; FAIL exits 1; insufficient evidence and setup errors exit 2 for this repository's CI wrapper. The underlying Maida CLI returns 0 for both PASS and INCONCLUSIVE, so the wrapper checks the verdict as well as the exit code. Trace storage is temporary; `gate-report.json` contains the local report and is gitignored.

GitHub runs **Application tests** and **Maida behavioral gate** for PRs and pushes to `main`. The gate reads policy and baseline from the PR's base commit. Changes to the policy, baseline, workflow, or gate runner require separate review and leave the PR check red; this repository does not implement an acceptance protocol for those changes. Configure branch protection to require both named checks and review of workflow changes before relying on these checks to prevent merges. A behavioral PASS covers the observed task and configured responsibilities; it does not replace application correctness tests or establish live-model reliability.

See [the scenario guide](scenarios/README.md) for small changes to create and submit manually with `gh`.
