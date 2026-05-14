#!/usr/bin/env python3
# orchestrator.py
#
# PURPOSE
#   Ingest architecture documents (PDF, DOCX, PPTX, Excel, images, CSV, TXT, MD)
#   and run a 3-stage Gemini analysis pipeline:
#     Stage 1 — Corpus intake and structured indexing
#     Stage 2 — Architecture gap analysis
#     Stage 3 — Internet-enabled interactive chat advisor
#
# OUTPUTS
#   <out>/01_Index_<timestamp>.md
#   <out>/02_Gap_Analysis_<timestamp>.md
#   <out>/chat_transcript_<timestamp>.md
#
# RUN
#   python orchestrator.py --folder "<docs_dir>" --out "<output_dir>"

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
import docx
from pptx import Presentation
import pymupdf4llm
import shutil as _shutil

from dotenv import load_dotenv

load_dotenv()

_PACKAGE_DIR = Path(__file__).resolve().parent


def _resolve_tesseract() -> str:
    cmd = os.getenv("TESSERACT_CMD")
    if cmd:
        return cmd
    found = _shutil.which("tesseract")
    if found:
        return found
    raise EnvironmentError(
        "Tesseract not found. Set TESSERACT_CMD in your .env file, "
        "e.g. TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe, "
        "or ensure tesseract is on your system PATH."
    )


import pytesseract
pytesseract.pytesseract.tesseract_cmd = _resolve_tesseract()

from PIL import Image

from gemini_runner import GeminiRunner


def extract_text(p: Path) -> str:
    ext = p.suffix.lower()
    try:
        content = ""
        if ext == ".pdf":
            content = pymupdf4llm.to_markdown(str(p))
        elif ext in {".xlsx", ".xls"}:
            df_dict = pd.read_excel(p, sheet_name=None)
            content = "\n".join(
                [f"### Sheet: {n}\n{df.to_markdown(index=False)}" for n, df in df_dict.items()]
            )
        elif ext == ".docx":
            doc = docx.Document(p)
            content = "\n".join([para.text for para in doc.paragraphs])
        elif ext == ".pptx":
            prs = Presentation(p)
            content = "\n".join(
                [
                    shape.text
                    for slide in prs.slides
                    for shape in slide.shapes
                    if hasattr(shape, "text")
                ]
            )
        elif ext in {".png", ".jpg", ".jpeg"}:
            content = f"[OCR DATA]: {pytesseract.image_to_string(Image.open(p))}"
        elif ext in {".csv", ".txt", ".md"}:
            if ext == ".csv":
                content = pd.read_csv(p).to_markdown(index=False)
            else:
                content = p.read_text(encoding="utf-8", errors="ignore")

        return f"\n\n=== START OF FILE: {p.name} ===\n{content}\n=== END OF FILE: {p.name} ===\n"
    except Exception as e:
        return f"[Error extracting {p.name}: {str(e)}]"


def run_sequential_analysis(
    docs_text: str,
    file_list: list,
    project: str,
    location: str,
    model: str,
    output_dir: str,
) -> None:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    personas_dir = _PACKAGE_DIR / "personas"

    # Stage 1: Indexing
    print(f"i STAGE 1: Indexing {len(file_list)} files...")
    p1 = (personas_dir / "Persona_01_Arch_Corpus_Intake_and_Indexer.md").read_text()
    indexer = GeminiRunner(
        agent_name="Indexer",
        instruction=p1,
        model=model,
        vertex_project=project,
        vertex_location=location,
    )
    index_results = indexer.ask(f"FILES: {file_list}\n\nCONTENT:\n{docs_text[:1_000_000]}")
    (out_path / f"01_Index_{timestamp}.md").write_text(index_results)

    # Stage 2: Gap Analysis
    print("i STAGE 2: Performing architecture gap analysis...")
    p2 = (personas_dir / "Persona_02_Arch_Gap_Analyst.md").read_text()
    analyst = GeminiRunner(
        agent_name="Analyst",
        instruction=p2,
        model=model,
        vertex_project=project,
        vertex_location=location,
    )
    gap_analysis = analyst.ask(f"INDEX:\n{index_results}")
    (out_path / f"02_Gap_Analysis_{timestamp}.md").write_text(gap_analysis)
    print(f"\n--- INITIAL GAP ANALYSIS ---\n{gap_analysis}\n")

    # Stage 3: Interactive Chat (Internet Enabled)
    print("i STAGE 3: Initializing research-enabled advisor...")
    p3 = (personas_dir / "Persona_03_Arch_Interactive_Chat_Advisor.md").read_text()
    advisor = GeminiRunner(
        agent_name="Advisor",
        instruction=p3,
        model=model,
        vertex_project=project,
        vertex_location=location,
        use_search=True,
    )

    transcript_path = out_path / f"chat_transcript_{timestamp}.md"
    log = f"# ARCH REVIEW RESEARCH SESSION: {timestamp}\n# FILES: {file_list}\n\n"

    while True:
        try:
            u_input = input("\nYou: ").strip()
            if not u_input or u_input.lower() in {"exit", "quit"}:
                break
            response = advisor.ask(
                f"SYSTEM: Use internal context and internet research. USER: {u_input}"
            )
            log += f"**User:** {u_input}\n\n**Gemini:** {response}\n\n---\n"
            transcript_path.write_text(log)
            print(f"\nGemini: {response}")
        except KeyboardInterrupt:
            break


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Architecture document review and gap analysis."
    )
    parser.add_argument("--folder", required=True, help="Directory containing architecture documents")
    parser.add_argument("--out", required=True, help="Output directory for analysis reports")
    args = parser.parse_args()

    project = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("VERTEX_PROJECT"))
    location = os.getenv("GOOGLE_CLOUD_LOCATION", os.getenv("VERTEX_LOCATION", "us-central1"))
    model = os.getenv("MODEL_NAME", "gemini-2.5-pro")

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"X Folder not found: {folder}", file=sys.stderr)
        raise SystemExit(1)

    full_text = ""
    f_names: list = []

    for f in sorted(folder.rglob("*")):
        if f.is_file() and not f.name.startswith((".", "~$")):
            print(f"  → [INGESTING] {f.name}")
            data = extract_text(f)
            if data:
                full_text += data
                f_names.append(f.name)

    run_sequential_analysis(full_text, f_names, project, location, model, args.out)


if __name__ == "__main__":
    main()
