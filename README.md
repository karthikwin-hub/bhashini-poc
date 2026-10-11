# Bhashini Sovereign Multilingual Platform (PoC)

A sovereign multilingual voice and text platform powered by **Project Bhashini** Digital Public Infrastructure (DPI) under MeitY, built using **Specification-Driven Development (SDD)** with **GitHub Spec Kit** and the **Agentic Delivery Kit**.

> **Humans steer · agents execute · sensors decide · humans accept.**

---

## 1. Overview & Architecture

This repository delivers an enterprise-grade multilingual middleware application integrating Bhashini's ULCA and Dhruva inference pipelines (ASR speech recognition, NMT machine translation, and TTS text synthesis) with messaging channels (Meta WhatsApp Cloud API) and web clients.

Key architectural characteristics:
- **Sovereign AI Infrastructure**: Dynamically negotiates ULCA compute pipelines, routing Indic vernacular tasks to sovereign clusters.
- **FastAPI Core**: High-concurrency async endpoints with background task orchestration for voice and text message processing.
- **Strict Separation of Concerns**: Pure domain logic (`src/domain/`), isolated external adapters (`src/adapters/`), and transport routing (`src/api/`).

---

## 2. Specification-Driven Development (SDD) Harness

This repository is governed by the **Agentic Delivery Kit (v1.0.2)** preset and workflows on top of **GitHub Spec Kit**:

- **The Constitution** ([`.specify/memory/constitution.md`](file:///.specify/memory/constitution.md)): 10 core principles ratified for quality, security, architecture, and verification.
- **The Map** ([`AGENTS.md`](file:///AGENTS.md)): Context-engineered guiding rules and output contract for AI agents (Cursor, Claude Code, Copilot).
- **Architecture Boundaries** ([`docs/ARCHITECTURE.md`](file:///docs/ARCHITECTURE.md)): Strict module ownership map.
- **The Sensors** ([`harness.toml`](file:///harness.toml)):
  - Format (`uv run ruff format --check .`)
  - Lint (`uv run ruff check .`)
  - Unit tests (`uv run pytest -q tests/unit`)
  - Acceptance tests (`uv run pytest -q tests/acceptance`)
  - Traceability (`scripts/harness/check_traceability.py`)
  - Test Integrity (`scripts/harness/check_test_integrity.py`)

---

## 3. Quick Start

### Prerequisites
- Python 3.12+
- `uv` (Fast Python package manager)
- `specify-cli` (GitHub Spec Kit CLI)

### Installation
```bash
# Clone and sync dependencies
uv sync
```

### Verification & Sensor Commands
```bash
# Check repository readiness
python scripts/harness/harness_doctor.py

# Inner-loop check (format + lint + unit tests)
python scripts/harness/verify.py --fast

# Full verification (format + lint + unit + acceptance + traceability + test integrity)
python scripts/harness/verify.py

# Run unit tests
uv run pytest -q tests/unit

# Run acceptance tests
uv run pytest -q tests/acceptance

# Run local development server
uv run uvicorn src.api.app:app --reload --port 8000
```

---

## 4. Delivery Lanes & Spec Kit Commands

| Lane | Purpose | Process |
|---|---|---|
| **0 Chore** | Minor fixes, configs, docs | Task → PR with `verify.py` evidence |
| **1 Bug** | Defect fix | `/speckit.bug.assess` → `/speckit.bug.fix` → `/speckit.bug.test` |
| **2 Small Change** | Low-risk single module change | `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement` → `/speckit.converge` |
| **3 Feature** | Cross-module, new contracts/data | Full SDD flow with Gates G1–G4 (or `agentic-sdd` workflow) |
| **4 Idea** | Feasibility / exploration | `/speckit.assess.intake` → `/speckit.assess.research` → `/speckit.assess.define` → `/speckit.assess.shape` → `/speckit.assess.decide` |
| **Spike** | Fast discovery & prototyping | Throwaway branch, **never merged**; learning captured in a spec |

---

## 5. Coding Agent Integrations
The repository is pre-configured with agent skills and guardrails across multiple interfaces:
- **Cursor**: Skills registered in `.cursor/skills/`
- **Claude Code**: Settings and skills in `.claude/`
- **GitHub Copilot**: Agent roles, instructions, and hooks in `.github/`
