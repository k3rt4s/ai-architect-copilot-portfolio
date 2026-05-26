# Portfolio sample

This repository is one of the public portfolio extracts published from a private commercial monorepo. It is intentionally non-functional.

## What is here

- The architecture, design rationale, and pipeline shape, in `README.md`.
- The document-ingestion layer and the GeminiRunner SDK wrapper, fully readable, so a reviewer can assess code style, naming, error handling, and SDK-integration design.
- Function signatures and docstrings for the three-stage orchestration, so the interface and contract are visible.

## What is withheld

- The body of `run_sequential_analysis` in `orchestrator.py`. It raises `NotImplementedError` on call. The production stage orchestration is proprietary.
- The three persona prompts under `personas/`. The files are placeholders that describe what a working prompt covers. The production prompts are proprietary.

## Why

Running this repository end-to-end would constitute a working product. The persona prompts and the tuned stage sequence are the result of meaningful engineering investment and remain the property of the author. The surrounding scaffolding is published so portfolio reviewers can evaluate the work without enabling reproduction.

## License

See `LICENSE`. The source is published for review only. No use, copy, modification, distribution, or commercial reuse is licensed.

## Other portfolio samples

Other repositories on this account that follow this same pattern carry the `-portfolio` suffix and contain a `PORTFOLIO_SAMPLE.md` file at the root. Public repositories without that suffix and without that file are full open-source tools and are licensed under their own stated terms.
