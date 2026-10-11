---
name: offer-quality-gate
description: Validate a German craftsperson quotation generator change for exact arithmetic, input safety, PDF generation and regression coverage before merging.
---

# Offer Quality Gate

When changing pricing, quote content or PDF rendering:

1. Confirm money calculations use Decimal and line rounding is ROUND_HALF_UP to cents.
2. Inspect non-finite numbers, negative prices, blank descriptions and zero quantities.
3. Check that offer totals in UI, PDF and TXT share the same calculation result.
4. Ensure any AI text generation cannot silently modify totals or contract terms.
5. Ensure missing external credentials do not block deterministic core functions.
6. Run python -m unittest discover -s tests -v and python -m compileall -q app.py offer_engine.py.
7. Review PDF text extraction for currency, quantity and wrapping. Report facts and limitations explicitly.
