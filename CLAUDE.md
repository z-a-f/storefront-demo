# Storefront agent instructions

Read `AGENTS.md` and `task.md` before editing. This checkout ships a small storefront: VIP customers always receive free shipping, and standard orders receive free shipping from $50.

- Run the full regression suite after every source edit.
- Use `python -m unittest tests.test_shipping tests.test_orders tests.test_server -q` for application verification.
- Do not refresh a regression expectation to make an implementation defect pass.

The local `.mcp.json` deliberately enables no external servers; this task needs only repository files and local tests.
