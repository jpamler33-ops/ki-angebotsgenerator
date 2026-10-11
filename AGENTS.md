# Coding agent rules — Angebotsgenerator

Goal: deliver the smallest safe, testable increment; do not rewrite the existing app unnecessarily.

1. Read `offer_engine.py`, `app.py`, and `tests/test_offer_engine.py` before editing.
2. Reproduce the reported bug with a failing test. Fix root cause, then rerun tests.
3. Price, quantities, VAT and gross totals **must** be calculated with `Decimal` in `offer_engine.py`; never delegate arithmetic to an LLM.
4. A failed/missing external AI API may not block deterministic calculations or PDF export.
5. Treat input as untrusted: validate every position; fail closed instead of silently skipping invalid rows; escape any markup in PDFs.
6. Never commit credentials, contact lists, customer records, `.env`, or fake testimonials.
7. Do not automatically send customer emails or perform paid API calls without explicit consent.
8. Keep user text in German. Run `python -m unittest discover -s tests -v` and `python -m compileall -q app.py offer_engine.py` (install `requirements-dev.txt` first) before proposing a merge.
9. Final report: ROOT CAUSE → CHANGE → TESTS → RESULT → REMAINING RISKS.

Potential security and tax details must be verified by a qualified person; never claim this prototype guarantees legal compliance.