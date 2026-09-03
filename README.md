# AI Debate

A local multi-model debate engine for structured, iterative reasoning with bounded context.

> **Current status:** Core protocol refactored around explicit roles, a real moderator, 10-round segments, health checks, and context compaction.

## Model topology

| Role | Model | Endpoint | Runtime | Primary responsibility |
|---|---|---|---|---|
| Moderator | `gemma4Coding-12B-Q4_K_M.gguf` | `http://127.0.0.1:8081/v1` | CPU | Coordinate rounds, evaluate arguments, detect agreement/conflict, maintain durable state, produce segment summaries |
| Agent 1 | `Qwen3-8B-Q5_K_M.gguf` | `http://127.0.0.1:8080/v1` | GPU | Constructive systems analyst and solution strategist |
| Agent 2 | `qwen2.5-coder-7b-instruct-q6_k.gguf` | `http://127.0.0.1:8082/v1` | CPU | Adversarial critic / red-team analyst |

`StupidModel` has been removed from the active architecture.

**Important launch-script alignment:** the role assignment above is authoritative. The Moderator server on port `8081` must run Gemma 4 Coding 12B. Agent 2 on port `8082` must run Qwen2.5-Coder 7B. If local `.bat` files still contain the opposite assignment, update them before testing.

Model identity and role logic are separate in `config.py`, so roles can be reassigned later without redesigning the debate engine.

## Agent roles

### Agent 1 — Constructive Strategist

- Builds the strongest coherent solution.
- Uses systems thinking, feasibility, evidence, and concrete proposals.
- Directly addresses the current mission and Agent 2's latest critique.
- Advances the discussion instead of repeating previous ideas.

### Agent 2 — Adversarial Critic

- Stress-tests Agent 1's claims and assumptions.
- Searches for contradictions, failure modes, hidden costs, and trade-offs.
- Concedes points when justified.
- Produces better alternatives when criticism exposes a weakness.

Neither agent is the moderator and neither agent is responsible for the canonical debate state.

## Moderator responsibilities

The Moderator is an active protocol controller, not a simple summarizer. For every round it:

1. Selects the most valuable mission for the round.
2. Forces the agents toward a specific unresolved issue or useful extension.
3. Evaluates both contributions after the exchange.
4. Extracts consensus, disagreements, new proposals, risks, resolved issues, and open questions.
5. Identifies the next direction of investigation.
6. Produces the master summary at the end of the segment.

Python owns the canonical `DebateState`; the Moderator supplies state deltas rather than replacing the state wholesale.

## Segment protocol

A segment always contains **10 rounds**:

```text
Question
   ↓
Segment N
   ├─ Round 1: Moderator mission → Agent 1 → Agent 2 → Moderator evaluation
   ├─ Round 2: Moderator mission → Agent 1 → Agent 2 → Moderator evaluation
   ├─ ...
   └─ Round 10: Moderator mission → Agent 1 → Agent 2 → Moderator evaluation
   ↓
Moderator Master Summary
   ↓
User: Stop OR Continue
```

If the user continues:

```text
Master Summary + durable Debate State
             ↓
      Python compacts context
             ↓
   Old live transcript discarded
             ↓
        Fresh Segment N+1
             ↓
Moderator mission → Agent 1 → Agent 2 → ...
```

The next segment never receives the previous live transcript. Only the original question and durable state are carried forward.

## Context management

`DebateState.arguments` contains only the live transcript for the current segment. `compact()` clears those arguments and increments the segment number. Durable fields such as consensus, disagreements, proposals, risks, decisions, and open questions remain available to the next segment.

This prevents unbounded context growth and prevents accidental transcript leakage between segments.

## Health checks

Before a debate starts, the application checks all three local OpenAI-compatible endpoints. A debate does not begin when any required server is unavailable.

The client also preserves `finish_reason`, usage metadata, and the raw response for diagnostics. Empty or malformed model responses fail safely instead of silently corrupting debate state.

## Architecture

```text
ai_debate/
├── app.py                    # CLI entry point and lifecycle
├── config.py                 # Model/role and debate configuration
├── requirements.txt
├── .env.example
└── debate/
    ├── __init__.py
    ├── engine.py             # 10-round protocol state machine
    ├── models.py             # DebateState and Argument
    ├── llm_client.py         # Local OpenAI-compatible adapter + health check
    ├── prompts.py            # Role-specific prompts and moderator protocol
    ├── context_manager.py    # Durable state and transcript compaction
    └── moderator.py          # Mission, evaluation, state delta, summary
```

## Configuration

Defaults are defined in `config.py` and can be overridden through environment variables. See `.env.example`.

Current defaults:

```text
Moderator: 127.0.0.1:8081 → Gemma4Coding-12B-Q4_K_M
Agent 1:   127.0.0.1:8080 → Qwen3-8B-Q5_K_M
Agent 2:   127.0.0.1:8082 → qwen2.5-coder-7b-instruct-q6_k
Rounds: 10 per segment
```

## Run

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Start the three local llama-server instances with the role/port assignment above, then:

```bash
python app.py
```

The application performs a health check first, runs exactly 10 rounds, asks whether to continue, and when continued starts the next segment from compact durable state without restarting llama-server.

## Scope

The current repository focuses on the core protocol and local-model adapter. A richer Web UI can be layered on top of the same engine without changing the debate/state architecture.
