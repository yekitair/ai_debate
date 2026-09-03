from __future__ import annotations

import json
import queue
import threading
from dataclasses import dataclass, field

from flask import Flask, Response, jsonify, render_template, request, stream_with_context

from config import AGENT_1, AGENT_2, DEBATE, MODERATOR
from debate.engine import DebateEngine, DebateStopped
from debate.llm_client import LLMClient, LLMError
from debate.models import DebateState
from debate.moderator import Moderator

app = Flask(__name__)


@dataclass
class Session:
    state: DebateState | None = None
    status: str = "idle"
    summary: str = ""
    error: str = ""
    stop_event: threading.Event = field(default_factory=threading.Event)
    events: queue.Queue = field(default_factory=queue.Queue)
    thread: threading.Thread | None = None
    lock: threading.RLock = field(default_factory=threading.RLock)


SESSION = Session()


def build_engine() -> DebateEngine:
    return DebateEngine(
        LLMClient(AGENT_1),
        LLMClient(AGENT_2),
        Moderator(LLMClient(MODERATOR), DEBATE.moderator_max_tokens, DEBATE.summary_max_tokens),
        DEBATE.rounds_per_segment,
        DEBATE.agent_max_tokens,
    )


def emit(event_type: str, **payload: object) -> None:
    SESSION.events.put({"type": event_type, **payload})


def state_payload() -> dict[str, object]:
    state = SESSION.state
    if state is None:
        return {"segment": 0, "round": 0, "status": SESSION.status}
    return {
        "segment": state.segment_number,
        "round": state.round_number,
        "status": SESSION.status,
        "consensus": state.consensus,
        "disagreements": state.disagreements,
        "open_questions": state.open_questions,
        "decisions": state.decisions,
        "proposals": state.proposals,
        "risks": state.risks,
        "discussed_topics": state.discussed_topics,
        "durable_summary": state.durable_summary,
    }


def drain_events() -> None:
    while True:
        try:
            SESSION.events.get_nowait()
        except queue.Empty:
            return


def run_segment_background() -> None:
    engine = build_engine()
    with SESSION.lock:
        SESSION.status = "running"
        SESSION.error = ""
    emit("segment_start", segment=SESSION.state.segment_number, rounds=DEBATE.rounds_per_segment)
    try:
        result = engine.run_segment(SESSION.state, stop_event=SESSION.stop_event, on_event=emit)
        summary = str(result["summary"]["text"])
        with SESSION.lock:
            SESSION.summary = summary
            SESSION.status = "waiting"
        emit("segment_complete", segment=result["segment"], rounds=len(result["rounds"]), summary=summary, state=state_payload())
    except DebateStopped:
        with SESSION.lock:
            SESSION.status = "stopped"
        emit("stopped", reason="Debate stopped by user.", state=state_payload())
    except LLMError as exc:
        with SESSION.lock:
            SESSION.status = "error"
            SESSION.error = str(exc)
        emit("error", message=str(exc), state=state_payload())
    except Exception as exc:
        with SESSION.lock:
            SESSION.status = "error"
            SESSION.error = f"Unexpected error: {exc}"
        emit("error", message=SESSION.error, state=state_payload())


def start_thread() -> None:
    SESSION.stop_event.clear()
    SESSION.thread = threading.Thread(target=run_segment_background, daemon=True)
    SESSION.thread.start()


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/health")
def api_health():
    health = build_engine().health_check()
    return jsonify({"ok": all(bool(item.get("ok")) for item in health.values()), "models": health})


@app.get("/api/status")
def api_status():
    with SESSION.lock:
        return jsonify({"status": SESSION.status, "summary": SESSION.summary, "error": SESSION.error, "state": state_payload()})


@app.post("/api/start")
def api_start():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({"ok": False, "error": "Question is required."}), 400
    with SESSION.lock:
        if SESSION.status in {"starting", "running", "stopping"}:
            return jsonify({"ok": False, "error": "A debate is already running."}), 409

    engine = build_engine()
    health = engine.health_check()
    if not all(bool(item.get("ok")) for item in health.values()):
        return jsonify({"ok": False, "error": "One or more local LLM servers are unavailable.", "models": health}), 503

    with SESSION.lock:
        drain_events()
        SESSION.state = DebateState(question=question)
        SESSION.status = "starting"
        SESSION.summary = ""
        SESSION.error = ""
        SESSION.stop_event.clear()
    emit("health", models=health)
    emit("question", question=question)
    start_thread()
    return jsonify({"ok": True, "state": state_payload()})


@app.post("/api/continue")
def api_continue():
    with SESSION.lock:
        if SESSION.status != "waiting" or SESSION.state is None:
            return jsonify({"ok": False, "error": "Continue is available only after a completed segment."}), 409
        SESSION.state.compact(SESSION.summary)
        SESSION.summary = ""
        SESSION.status = "starting"
        SESSION.error = ""
        SESSION.stop_event.clear()
    emit("compacted", state=state_payload(), message="Previous live transcript discarded; durable state retained.")
    start_thread()
    return jsonify({"ok": True, "state": state_payload()})


@app.post("/api/stop")
def api_stop():
    with SESSION.lock:
        if SESSION.status not in {"running", "starting"}:
            return jsonify({"ok": True, "status": SESSION.status})
        SESSION.stop_event.set()
        SESSION.status = "stopping"
    emit("stopping", message="Stop requested; the current model call will finish before the engine exits.")
    return jsonify({"ok": True})


@app.get("/stream")
def stream():
    @stream_with_context
    def generate():
        while True:
            event = SESSION.events.get()
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True, use_reloader=False)
