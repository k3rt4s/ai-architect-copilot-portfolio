# Persona 01 — Corpus Intake and Indexer (placeholder)

> This file is a portfolio-demo placeholder. The production prompt is proprietary and not published here.

## What this stage does

Stage 1 receives the extracted text from every supported document type (PDF, DOCX, PPTX, XLSX, CSV, images via OCR, plain text, Markdown) and produces a structured index of the architecture corpus. The index lists each artifact with a short summary, a content-type classification, and cross-references between documents so stage 2 can reason about the corpus as a whole rather than file-by-file.

## What a working prompt covers

A production prompt for this stage typically covers:

- Output schema (Markdown headings, table columns, cross-reference notation).
- How to summarize without losing technical specificity.
- How to classify artifacts (system diagram, sequence diagram, data model, deployment, threat model, requirement, runbook, decision record, and so on).
- How to handle conflicting or duplicate information across documents.
- How to flag missing-but-expected artifact types so stage 2 can use that as a gap signal.

Replace this file with your own persona prompt to run the pipeline end-to-end.
