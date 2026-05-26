# ai-architect-copilot

> **Portfolio demo.** This repository is the orchestration and pipeline scaffolding for a commercial tool. The persona prompts that drive the three Gemini stages are intentionally replaced with placeholders so the code can be inspected and the pattern reused, while the production prompts that determine review quality remain proprietary.

A three-stage Gemini pipeline that reviews an architecture or design corpus and produces an operational and security gap analysis, then exposes an interactive chat advisor the solution owner can rehearse with before walking into a real Architecture Review Board.

Point it at a folder of mixed-format design artifacts (PDF, DOCX, PPTX, XLSX, CSV, PNG/JPG, TXT, MD) and it:

1. Ingests every file with the right extractor and builds a structured index.
2. Runs a gap analysis against architectural standards and writes a Markdown report.
3. Opens an internet-enabled chat session where the user can probe weaknesses, justify trade-offs, and iterate before review-board day.

## Why this exists

Architecture review boards bottleneck on first-pass reading. A reviewer spends two hours absorbing slides and diagrams before asking the questions that actually matter. This tool takes that first pass off the human reviewer's plate and surfaces the same questions to the proposer up-front, so the live review is spent on judgment instead of orientation.

## Pipeline

| Stage                        | Persona file                                            | What it produces                                                                           |
| ---------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 1. Corpus intake and indexer | `personas/Persona_01_Arch_Corpus_Intake_and_Indexer.md` | `01_Index_<timestamp>.md` — every document summarized and cross-linked                     |
| 2. Gap analyst               | `personas/Persona_02_Arch_Gap_Analyst.md`               | `02_Gap_Analysis_<timestamp>.md` — operational and security gaps against standard patterns |
| 3. Interactive chat advisor  | `personas/Persona_03_Arch_Interactive_Chat_Advisor.md`  | `chat_transcript_<timestamp>.md` — Google-Search-enabled Q&A session                       |

The persona prompts are plain Markdown. Edit them in place to shift the review framework (e.g. from generic architecture to NIST 800-53, ISO 27001, SOC 2 CC, or a house standard) without touching code.

## Supported inputs

| Extension                 | Extraction method                 |
| ------------------------- | --------------------------------- |
| `.pdf`                    | pymupdf4llm (Markdown output)     |
| `.docx`                   | python-docx paragraph text        |
| `.pptx`                   | python-pptx shape text            |
| `.xlsx` / `.xls`          | pandas (Markdown table per sheet) |
| `.csv`                    | pandas Markdown table             |
| `.png` / `.jpg` / `.jpeg` | Tesseract OCR                     |
| `.txt` / `.md`            | Raw UTF-8                         |

## Running this sample

This repository is intentionally non-functional. The CLI exists so a reviewer can see the argument parsing, document-ingestion layer, and overall control flow, but the analysis stage is stubbed.

Running

```bash
python orchestrator.py --folder "<docs_dir>" --out "<output_dir>"
```

will install dependencies, ingest every supported file under `<docs_dir>` via the extraction layer, print a portfolio-sample notice, and exit with code 2 before reaching the three-stage Gemini pipeline. The persona prompts under `personas/` are also placeholders; the production prompts are proprietary. See `PORTFOLIO_SAMPLE.md` for the full disclosure.

Setup, if you want to exercise the ingestion path on your own documents:

```bash
git clone https://github.com/k3rt4s/ai-architect-copilot-portfolio
cd ai-architect-copilot-portfolio
python -m venv .venv && . .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Tech stack

- Gemini 2.5 Pro on Vertex AI, called through `google-adk` for session management and the Google Search tool binding in stage 3.
- pymupdf4llm, python-docx, python-pptx, pandas, Pillow + Tesseract for the document polymorphism layer.
- A thin `GeminiRunner` wrapper (`gemini_runner.py`) so the orchestrator stays focused on prompts and document handling, not SDK plumbing.

## License

All Rights Reserved. Published for portfolio review only. See `LICENSE` and `PORTFOLIO_SAMPLE.md`.
