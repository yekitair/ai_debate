# AI Debate

A local multi-model debate system that orchestrates two debate agents and a dedicated moderator.

> **Status:** Initial architecture / implementation scaffold
>
> This project is intentionally independent of BAES for now. A future BAES adapter may be added without coupling the core debate engine to BAES.

## Model topology

| Role | Model | Endpoint | Runtime |
|---|---|---|---|
| Moderator | StupidModel-6b | `http://127.0.0.1:8081/v1` | CPU |
| Agent 1 | Qwen3-8B | `http://127.0.0.1:8080/v1` | GPU |
| Agent 2 | gemma4Coding-12B | `http://127.0.0.1:8082/v1` | CPU |

The endpoints are configurable through environment variables or `config.py`.

## Core debate protocol

1. The user submits a debate question/mission.
2. The engine creates an explicit debate state.
3. Agent 1 and Agent 2 argue opposing positions.
4. The Moderator observes the exchange and controls the protocol; it is not a debate contestant.
5. A debate segment contains **10 rounds**.
6. At the end of the 10th round, the Moderator produces a structured summary/state.
7. The user chooses whether to stop or continue for another 10 rounds.
8. Before continuation, Python compacts/clears the live conversational context. The next segment receives only the durable summary/state required to continue.

This prevents unbounded context growth while preserving the logical state of the debate.

## Architecture

```text
ai_debate/
├── app.py                    # Application entry point
├── config.py                 # Runtime/model configuration
├── requirements.txt
├── .env.example
└── debate/
    ├── __init__.py
    ├── engine.py             # Debate state machine / orchestration
    ├── models.py             # Typed domain models
    ├── llm_client.py         # OpenAI-compatible local LLM adapter
    ├── prompts.py            # Role-specific prompt construction
    ├── context_manager.py    # Context compaction and continuation state
    └── moderator.py          # Moderator-specific logic
```

### Design principles

- **Separation of concerns:** orchestration, model access, prompts, and state management are independent.
- **Provider neutrality:** models are accessed through an OpenAI-compatible HTTP adapter; the core engine does not know about llama-server internals.
- **Explicit state:** debate state is represented by typed objects rather than hidden prompt history.
- **Bounded context:** only the current 10-round segment is kept live; continuation uses a compact state package.
- **Moderator authority:** the moderator controls round progression, summaries, and protocol-level observations.
- **No BAES coupling:** BAES-specific behavior belongs in a future adapter, not in the core engine.

## Run

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Make sure the three local OpenAI-compatible servers are running, then:

```bash
python app.py
```

Configuration can be overridden with environment variables. See `.env.example`.

## Current implementation scope

The first implementation focuses on a reliable protocol engine and local-model adapter. UI/API layers can be added on top without changing the domain/state model.
