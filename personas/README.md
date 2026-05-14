# Personas

The three files in this directory drive the three pipeline stages. Each is a Markdown prompt that the orchestrator loads at runtime.

In this public repository the personas are placeholders that describe what a working prompt covers but do not include production prompt text. The orchestrator will run with the placeholders in place but the outputs will not be useful until each persona is replaced with a real prompt suited to your review framework.

| File                                           | Stage | Output                           |
| ---------------------------------------------- | ----- | -------------------------------- |
| `Persona_01_Arch_Corpus_Intake_and_Indexer.md` | 1     | `01_Index_<timestamp>.md`        |
| `Persona_02_Arch_Gap_Analyst.md`               | 2     | `02_Gap_Analysis_<timestamp>.md` |
| `Persona_03_Arch_Interactive_Chat_Advisor.md`  | 3     | `chat_transcript_<timestamp>.md` |
