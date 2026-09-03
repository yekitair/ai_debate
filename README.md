# AI Debate

A local multi-model debate system with an active Moderator, two deliberately different agents, bounded context, configurable round segments, human intervention notes, and a Persian RTL web interface.

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

## Roles

### Moderator — active protocol controller

The Moderator is **not** a simple summarizer. At the beginning of every round it chooses the most valuable mission, can incorporate a human operator note, forces progress, and then evaluates both contributions. It extracts consensus, disagreement, new proposals, risks, resolved issues, open questions, and the next direction. At the end of the configured segment it produces the Master Summary.

Python owns the canonical `DebateState`; the Moderator supplies incremental state information.

### Agent 1 — constructive strategist

Agent 1 builds the strongest technically coherent solution. It emphasizes feasibility, systems thinking, evidence, concrete proposals, and useful advancement.

### Agent 2 — adversarial critic

Agent 2 stress-tests assumptions, contradictions, failure modes, hidden costs, risks, and trade-offs. It concedes valid points when warranted and proposes better alternatives when criticism reveals a weakness. It does not disagree mechanically.

## Segment protocol

A Segment has a **user-configurable number of rounds**. The UI defaults to 10 and permits 1–100 rounds.

```text
Question
  ↓
Health-check all 3 LLM servers
  ↓
Segment N
  ├─ Round 1..N:
  │    Moderator Mission
  │      ↓
  │    Agent 1 → Agent 2
  │      ↓
  │    Moderator Evaluation / durable-state update
  ↓
Master Summary
  ↓
WAIT: Continue or Stop
```

The user also chooses a maximum output-token budget per model response (128–4096, default 1200). If a model reports `finish_reason=length`, the UI marks the response as truncated.

## Human operator notes

While a debate is running, the user can enter a note at any time. The note is queued in Python and is **not** sent to the agents. When the next Moderator turn begins:

1. Python archives the note with Segment/Round metadata.
2. The pending note is removed from the active queue.
3. The Moderator receives the archived note as a human instruction/observation.
4. The UI marks that the note was consumed.

Thus a note is read once by the Moderator and then no longer remains pending. The archived copy remains available for the Word export.

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

The next segment therefore does **not** receive the previous raw transcript. The three `llama-server` processes continue running; only Python-side debate context is reset. Durable fields include consensus, disagreements, proposals, risks, decisions, open questions, and discussed topics.

## Web UI

The application listens on:

```text
http://127.0.0.1:5000
```

It provides:

- Persian RTL question input
- configurable rounds per Segment
- configurable output-token budget
- health status for all three local servers
- Start / Stop / Continue
- live Segment and Round counters
- live Moderator missions/evaluations
- Agent 1 and Agent 2 responses
- human note input during the debate
- Master Summary
- durable state panels
- **Save Result as Word (.docx)** after at least one Segment completes

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

Then open:

```text
http://127.0.0.1:5000
```

## Project structure

```text
ai_debate/
├── app.py                    # Flask UI, API, SSE, session lifecycle, Word export
├── config.py                 # model roles and default/range settings
├── requirements.txt
├── .env.example
├── templates/index.html      # Persian RTL UI
├── static/app.js             # UI + SSE client
├── static/style.css
├── tests/test_debate_flow.py # deterministic protocol test
└── debate/
    ├── engine.py             # segment state machine
    ├── models.py             # DebateState and Argument
    ├── llm_client.py         # local OpenAI-compatible adapter + health check
    ├── prompts.py            # role-specific prompts and Moderator protocol
    ├── context_manager.py    # bounded durable context / transcript isolation
    └── moderator.py          # missions, evaluations, state deltas, summary
```

## Deterministic protocol test

The model-free test verifies configurable round counts, Moderator mission/evaluation flow, compaction, transcript isolation, and one-time human-note consumption.

Run:

```bash
python -m unittest discover -s tests -v
```

## Configuration

Defaults and valid ranges live in `config.py`. Environment variables in `.env.example` control defaults; the browser settings override them for each new debate.

```text
Moderator: 127.0.0.1:8081 → Gemma4Coding-12B-Q4_K_M
Agent 1:   127.0.0.1:8080 → Qwen3-8B-Q5_K_M
Agent 2:   127.0.0.1:8082 → qwen2.5-coder-7b-instruct-q6_k
Default rounds: 10
Allowed rounds: 1–100
Default output tokens: 1200
Allowed output tokens: 128–4096
Web UI: 127.0.0.1:5000
```

No cloud model or remote API is required by the architecture.
