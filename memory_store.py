"""Memory / state for StudyMate Agent. Simple JSON file store."""

import json
import os

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"runs": 0, "weak_topics": [], "history": []}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"runs": 0, "weak_topics": [], "history": []}


def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)


def update_after_run(goal, score_percent, weak_topics):
    mem = load_memory()
    mem["runs"] = mem.get("runs", 0) + 1
    old_weak = set(mem.get("weak_topics", []))
    old_weak.update(weak_topics)
    mem["weak_topics"] = sorted(old_weak)
    mem["history"].append({"goal": goal, "score": score_percent,
                           "weak": weak_topics})
    # keep last 20 only
    mem["history"] = mem["history"][-20:]
    save_memory(mem)
    return mem
