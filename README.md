# AI Debate

A local multi-model debate system with an active Moderator, two deliberately different agents, bounded context, 10-round segments, and a Persian RTL web interface.

## Final architecture

```text
Browser
   │
   ▼
127.0.0.1:5000  Flask Web UI
   │
   ├──► 127.0.0.1:8081  Gemma 4 Coding 12B   — Moderator / CPU
   ├──► 127.0.0.1:8080  Qwen3 8B             — Agent 1 / GPU
   └──► 127.0.0.1:8082  Qwen2.5-Coder 7B Q6  — Agent 2 / CPU
```

`StupidModel` is completely outside the active architecture.

| Role | Model | Endpoint | Runtime | Responsibility |
|---|---|---|---|---|
| Moderator | `gemma4Coding-12B-Q4_K_M.gguf` | `127.0.0.1:8081` | CPU | Control protocol, choose missions, evaluate rounds, maintain durable state, summarize segments |
| Agent 1 | `Qwen3-8B-Q5_K_M.gguf` | `127.0.0.1:8080` | GPU | Constructive systems analyst and solution strategist |
| Agent 2 | `qwen2.5-coder-7b-instruct-q6_k.gguf` | `127.0.0.1:8082` | CPU | Adversarial critic / red-team analyst |

The role assignment above is authoritative. If local BAT files use another assignment, correct them before starting the application.

## Roles

### Moderator — active protocol controller

The Moderator is **not** a simple summarizer. In every round it chooses the most valuable mission, forces progress, evaluates both contributions, extracts consensus/disagreement/new proposals/risks/resolved issues/open questions, and identifies the next direction. After Round 10 it produces the Master Summary.

Python owns the canonical `DebateState`; the Moderator supplies incremental state information.

### Agent 1 — constructive strategist

Agent 1 builds the strongest technically coherent solution. It emphasizes feasibility, systems thinking, evidence, concrete proposals, and useful advancement. It directly engages the current mission and Agent 2 rather than repeating old ideas.

### Agent 2 — adversarial critic

Agent 2 stress-tests assumptions, contradictions, failure modes, hidden costs, risks, and trade-offs. It concedes valid points when warranted and proposes better alternatives when criticism reveals a weakness. Its job is not to disagree mechanically.

## Exact segment protocol

Every segment is exactly 10 rounds:

```text
Question
  ↓
Health-check all 3 LLM servers
  ↓
Segment N
  ├─ Round 1: Moderator Mission → Agent 1 → Agent 2 → Moderator Evaluation
  ├─ Round 2: Moderator Mission → Agent 1 → Agent 2 → Moderator Evaluation
  ├─ ...
  └─ Round 10: Moderator Mission → Agent 1 → Agent 2 → Moderator Evaluation
  ↓
Moderator Master Summary
  ↓
WAIT: Continue or Stop
```

The UI streams missions, agent responses, Moderator evaluations, state changes, and the final summary live through Server-Sent Events.

## Context isolation and compaction

`DebateState.arguments` is the live transcript for the current segment only. It is never used as historical context for a later segment.

When **Continue** is selected:

```text
Master Summary + durable DebateState
              ↓
       Python compacts state
              ↓
   current live arguments = cleared
              ↓
       Segment N+1 starts
              ↓
Question + durable state only
```

The next segment therefore does **not** receive the previous raw transcript. The three `llama-server` processes continue running; only Python-side debate context is reset. Durable fields include consensus, disagreements, proposals, risks, decisions, open questions, and discussed topics. The context manager bounds accumulated state sent to models.

## Health and failure handling

Before starting a debate, Flask checks all three local servers. A missing required server prevents the debate from starting. The client preserves `finish_reason`, usage metadata, and raw response data for diagnostics.

Empty or malformed model responses fail safely. A user stop is handled separately from an LLM failure. If a model returns `finish_reason = length`, the UI marks that response as truncated.

## Web UI

The web application listens on:

```text
http://127.0.0.1:5000
```

It provides Persian RTL question input, model health, Start/Stop/Continue controls, live segment/round counters, Moderator missions/evaluations, both agent responses, Master Summary, durable state panels, and error reporting.

The Flask server does not start or restart local `llama-server` processes. Start those three servers separately.

## Launching the three llama-server instances

Use the model paths from your local machine. The required role/port mapping is:

### 1. Moderator — Gemma 4 Coding 12B — CPU — 8081

```bat
C:\VULKAN\llama-server.exe -m "<PATH>\gemma4Coding-12B-Q4_K_M.gguf" -ngl 0 -t 12 -c 10240 -fa on -b 2048 --host 0.0.0.0 --port 8081 -np 1
```

### 2. Agent 1 — Qwen3 8B — GPU — 8080

```bat
C:\VULKAN\llama-server.exe -m "<PATH>\Qwen3-8B-Q5_K_M.gguf" -ngl 999 -c 10240 -fa on -b 2048 --host 0.0.0.0 --port 8080 -np 1
```

### 3. Agent 2 — Qwen2.5-Coder 7B Q6 — CPU — 8082

```bat
C:\VULKAN\llama-server.exe -m "<PATH>\qwen2.5-coder-7b-instruct-q6_k.gguf" -ngl 0 -t 12 -c 10240 -fa on -b 2048 --host 0.0.0.0 --port 8082 -np 1
```

The exact local filename/path wins over the placeholder; the role-to-port mapping does not change.

## Install and run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Project structure

```text
ai_debate/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── style.css
├── tests/
│   └── test_debate_flow.py
└── debate/
    ├── engine.py
    ├── models.py
    ├── llm_client.py
    ├── prompts.py
    ├── context_manager.py
    └── moderator.py
```

## Deterministic protocol test

The model-free test verifies: 10 rounds → 20 live agent arguments → 10 Moderator missions → 10 Moderator evaluations → 1 segment summary → compaction → transcript cleared → segment increment → another 10-round segment.

Run:

```bash
python -m unittest discover -s tests -v
```

## Configuration

Defaults live in `config.py` and can be overridden through `.env.example`:

```text
Moderator: 127.0.0.1:8081 → Gemma4Coding-12B-Q4_K_M
Agent 1:   127.0.0.1:8080 → Qwen3-8B-Q5_K_M
Agent 2:   127.0.0.1:8082 → qwen2.5-coder-7b-instruct-q6_k
Rounds: 10 per segment
Web UI: 127.0.0.1:5000
```

No cloud model or remote API is required by the architecture.
