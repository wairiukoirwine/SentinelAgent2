# Project context

**SentinelAgent: Design and Evaluation of a Policy-Enforced Security Gateway Against Indirect Prompt Injection in a Simulated AI Agent.**
DAI034 Capstone, Track C (Secure AI Applications), Africa International University, SCET. Supervisor: Dr. Jared Mayeika. Submission: November 2026.

## Source of truth (in priority order)

1. **Approved Chapter One proposal** (`SentinelAgent_Chapter1_Proposal.docx`, held in the project workspace): objectives, scope, roles, deliverables.
2. **`PROJECT_SPEC.txt`**: detailed build specification. Where it conflicts with the proposal (roles), the proposal wins (TD-001).
3. **This repository's docs**: `SYSTEM_ARCHITECTURE.md`, `TECHNICAL_DECISIONS.md`, `docs/`. Always verified against the code.

## Research question

For a small simulated document-reading agent: (1) how far does a mandatory tool-call gateway reduce unsafe actions, (2) how many normal tasks does it block by mistake, and (3) does a content detector add protection once the gateway is in place?

## Objectives and leads

| # | Objective | Lead |
|---|---|---|
| i | Architecture + labelled normal/attack scenarios with fake documents, two mock tools | Irwine |
| ii | Simulated agent + mandatory gateway returning ALLOW / BLOCK / REVIEW before any mock tool runs | Teddy |
| iii | Pretrained text classifier vs keyword baseline: precision, recall, confusion matrix on a separate test set | Benedict |
| iv | Compare four setups (none, content only, policy only, both) on attack success, normal completion, false blocks, decision time; dashboard | Teddy (dashboard: Irwine) |

## Hard boundaries

- Fake documents, fictional `example.test` recipients, mock `read_document` and `send_email` only. No real email, network, LLM API, or personal data.
- Pretrained classifier used as-is; only its threshold is tuned. No model training or fine-tuning.
- Free, local, laptop-CPU stack. No paid services.
- Final-test scenarios are never used for tuning.
- Results describe this simulated agent and corpus only. No claim of production protection.

## Current state

See `DEVELOPMENT_ROADMAP.md` for step status and `DEVELOPMENT_LOG.md` for the history of changes.
