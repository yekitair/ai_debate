# AI Debate

A local multi-model debate system with an active Moderator, two deliberately different agents, bounded context, configurable debate segments, human intervention notes, multilingual model output, and a Persian RTL web interface.

## Architecture

```text
Browser
   │
   ▼
127.0.0.1:5000  Flask Web UI
   │
   ├──► Moderator LLM
   ├──► Agent 1 LLM
   └──► Agent 2 LLM
```

The application is designed around three independent OpenAI-compatible local LLM endpoints. Their concrete models, executable locations, and machine-specific paths are runtime configuration details and are intentionally not documented here.

## Roles

### Moderator — protocol controller

The Moderator is not a simple summarizer. At the beginning of every round it chooses a precise mission, can incorporate a human operator note, evaluates both contributions, and updates the durable debate state.

It tracks:

- consensus
- disagreements
- new proposals
- risks and trade-offs
- resolved issues
- open questions
- next investigation focus

At the end of a segment it produces the Master Summary.

Python owns the canonical `DebateState`; the Moderator supplies incremental state information rather than owning the complete transcript.

### Agent 1 — constructive strategist

Builds the strongest technically coherent position, emphasizing feasibility, systems thinking, evidence, concrete proposals, and useful advancement.

### Agent 2 — adversarial critic

Stress-tests assumptions, contradictions, failure modes, hidden costs, risks, and trade-offs. It should concede valid points and propose better alternatives when appropriate rather than disagreeing mechanically.

## Segment protocol

A Segment contains a user-configurable number of rounds. The UI defaults to 10 and permits 1–100 rounds.

```text
Question
  ↓
Health-check the three LLM endpoints
  ↓
Segment N
  ├─ Round 1..N
  │    Moderator Mission
  │      ↓
  │    Agent 1 → Agent 2
  │      ↓
  │    Moderator Evaluation / state delta
  ↓
Master Summary
  ↓
WAIT: Continue or Stop
```

The user can also choose the maximum output-token budget for model responses (128–4096, default 1200). If a model reports `finish_reason=length`, the UI marks the response as truncated.

## Multilingual debates

The debate language can be selected as:

- Auto
- Persian
- English
- German
- French
- Chinese

In **Auto**, the application makes a lightweight language determination from the user's question. The selected language is propagated to the Moderator, both agents, round evaluations, missions, and the Master Summary.

Protocol markers used by the Moderator remain stable English markers for parser reliability; the natural-language content beneath them follows the selected debate language.

## Human operator notes

While a debate is running, the user can enter a note at any time. The note is queued in Python and is not sent directly to the agents.

When the next Moderator turn begins:

1. Python archives the note with Segment/Round metadata.
2. The pending note is removed from the active queue.
3. The Moderator receives the note as a human instruction/observation.
4. The UI records that the note was consumed.

The archived note remains available for Word export.

## Context isolation and compaction

`DebateState.arguments` is the live transcript for the current segment only. Raw historical arguments are not carried into a later segment.

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
Question + durable state
```

The LLM server processes remain running. Only the Python-side debate context is compacted/reset.

Durable state includes consensus, disagreements, proposals, risks, decisions, open questions, discussed topics, and next focus.

## Web UI

The application listens on:

```text
http://127.0.0.1:5000
```

It provides:

- Persian RTL interface
- debate-language selection
- configurable rounds per Segment
- configurable output-token budget
- health status for all three LLM endpoints
- Start / Stop / Continue
- live Segment and Round counters
- Moderator missions and evaluations
- Agent 1 and Agent 2 responses
- human note input during a debate
- Master Summary
- durable state panels
- Save Result as Word (`.docx`) after at least one Segment completes

The Flask application does not launch or restart the local LLM servers. They are external runtime dependencies.

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

The three configured OpenAI-compatible LLM endpoints must be running before starting a debate.

## Project structure

```text
ai_debate/
├── app.py                    # Flask UI, API, SSE, session lifecycle, Word export
├── config.py                 # endpoint roles and default/range settings
├── requirements.txt
├── .env.example
├── templates/index.html      # Persian RTL UI
├── static/app.js             # UI + SSE client
├── static/style.css
├── tests/test_debate_flow.py # deterministic protocol test
└── debate/
    ├── engine.py             # segment state machine
    ├── models.py             # DebateState and Argument
    ├── llm_client.py         # OpenAI-compatible adapter + health check
    ├── prompts.py            # role prompts and Moderator protocol
    ├── context_manager.py    # bounded durable context / transcript isolation
    └── moderator.py          # missions, evaluations, state deltas, summary
```

## Deterministic protocol test

The model-free test verifies the orchestration layer, including configurable round counts, Moderator mission/evaluation flow, compaction, transcript isolation, and one-time human-note consumption.

Run:

```bash
python -m unittest discover -s tests -v
```

## Configuration

Defaults and valid ranges live in `config.py`. Environment variables in `.env.example` define defaults, while the browser settings can override them for each new debate.

The repository deliberately avoids documenting machine-specific model filenames, executable paths, GPU/CPU assignments, and other local runtime details. Those belong to the user's local configuration, not to the project documentation.

No cloud model or remote API is required by the architecture.
