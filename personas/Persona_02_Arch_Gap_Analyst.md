# Persona 02 — Gap Analyst (placeholder)

> This file is a portfolio-demo placeholder. The production prompt is proprietary and not published here.

## What this stage does

Stage 2 reads the structured index produced by stage 1 and identifies operational and security gaps against architectural standards. It writes a Markdown gap-analysis report grouped by domain (resilience, identity, data protection, observability, supply chain, change management, and so on) with severity scoring and a recommended next action for each gap.

## What a working prompt covers

A production prompt for this stage typically covers:

- The review framework being applied (generic architecture, NIST 800-53, ISO 27001, SOC 2 CC, CIS Controls, or a house standard).
- Domain decomposition and which families to evaluate.
- A severity rubric distinct from "everything is high".
- How to phrase findings so a non-defensive design owner will engage with them.
- How to cite the corpus when a finding is grounded in a specific document, versus when it is grounded in the absence of evidence.
- When to recommend a hard remediation versus a compensating control.

Replace this file with your own persona prompt to run the pipeline end-to-end.
