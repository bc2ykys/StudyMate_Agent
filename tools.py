"""
StudyMate Agent - tools.py
All tools use only Python standard library.
No API key needed. Works offline.
Each tool returns a dict with status for failure handling.
"""

import re
import random


def retrieve_notes(query, knowledge_text):
    """Tool 1: Retrieval - search local knowledge base."""
    query_words = re.findall(r"[a-z]+", query.lower())
    stop = {"what", "is", "the", "a", "an", "of", "for", "to", "in", "on",
            "me", "my", "prepare", "test", "exam", "explain", "tell"}
    keywords = [w for w in query_words if w not in stop and len(w) > 2]

    if not keywords:
        return {"status": "empty",
                "message": "Query had no keywords. Try: agent, tools, memory, planning.",
                "chunks": []}

    lines = knowledge_text.split("\n")
    scored = []
    for line in lines:
        line_low = line.lower()
        score = sum(1 for k in keywords if k in line_low)
        # ignore headers, separators and very short fragments
        if score > 0 and len(line.strip()) > 40 and not line.strip().startswith("="):
            # longer informative lines rank higher
            scored.append((score * 10 + min(len(line.strip()), 200), line.strip()))

    scored.sort(reverse=True)
    top = [l for _, l in scored[:4]]

    # fallback: if too few hits, add key general notes so demo is rich
    if len(top) < 3:
        for line in lines:
            s = line.strip()
            if len(s) > 60 and s not in top and s[0].isdigit():
                top.append(s)
            if len(top) >= 3:
                break

    if not top:
        return {"status": "not_found",
                "message": "No matching notes found for: " + query,
                "chunks": []}

    return {"status": "ok", "message": f"Found {len(top)} chunks.",
            "chunks": top}


def make_summary(chunks):
    """Tool 2: Summarizer - compress retrieved chunks into study points."""
    if not chunks:
        return {"status": "error", "message": "Nothing to summarize.", "summary": ""}
    points = []
    for c in chunks[:4]:
        short = c.strip()
        if len(short) > 140:
            short = short[:140] + "..."
        points.append("- " + short)
    summary = "KEY POINTS:\n" + "\n".join(points)
    return {"status": "ok", "summary": summary}


def _parse_kb_questions(chunks):
    """Parse knowledge-base chunks into fill-in-the-blank questions.

    Strategy:
      1. Each numbered line is of the form  "N. <sentence>".
      2. Extract the FIRST significant noun-phrase (>3 chars, not a stop word)
         as the answer keyword, blank it out, and turn the sentence into a
         question with '______' in place of the keyword.
      3. The topic tag is derived from the answer keyword itself.

    Returns a list of {"q": ..., "a": ..., "topic": ...} dicts.
    """
    import re as _re
    stop = {"the", "this", "that", "what", "which", "with", "from", "into",
            "than", "then", "when", "where", "such", "each", "also", "only",
            "once", "been", "done", "they", "them", "their", "some", "more",
            "very", "most", "like", "will", "does", "have", "just"}
    questions = []
    for line in chunks:
        # strip leading number + dot
        body = _re.sub(r"^\d+\.\s*", "", line.strip())
        if len(body) < 30:
            continue
        words = _re.findall(r"[A-Za-z_]+", body)
        # pick first content word longer than 3 chars and not in stop list
        keyword = None
        for w in words:
            if len(w) > 3 and w.lower() not in stop:
                keyword = w
                break
        if keyword is None:
            continue
        # blank out the keyword (first occurrence, case-insensitive)
        blanked = _re.sub(_re.escape(keyword), "______", body, count=1,
                          flags=_re.IGNORECASE)
        q_text = "Fill in the blank: " + blanked
        questions.append({"q": q_text, "a": keyword.lower(),
                          "topic": keyword.lower()})
    return questions


# Static fallback bank (original hardcoded questions)
_STATIC_BANK = [
    {"q": "What is the 5-step loop followed by the StudyMate controller?",
     "a": "observe decide act evaluate adapt", "topic": "controller-loop"},
    {"q": "Which component stores past runs and weak topics?",
     "a": "memory", "topic": "memory"},
    {"q": "Name one tool the agent can call to get study material.",
     "a": "retrieve_notes", "topic": "tools"},
    {"q": "What does the agent do when web search fails once?",
     "a": "retry", "topic": "failure-handling"},
    {"q": "Why is an agent better than a one-shot chatbot for study?",
     "a": "plans tools evaluation memory", "topic": "agentic-vs-chatbot"},
]


def generate_quiz(chunks, level="easy"):
    """Tool 3: Quiz generator - dynamically builds questions from notes.

    Tries to parse the retrieved chunks into fill-in-the-blank questions.
    Falls back to the static bank if fewer than 3 dynamic questions are
    generated (e.g. chunks are too short or oddly formatted).
    """
    dynamic = _parse_kb_questions(chunks)
    if len(dynamic) >= 3:
        bank = dynamic
    else:
        bank = _STATIC_BANK  # safe fallback

    if level == "remedial":
        picked = bank[:2]  # easier retry set
    else:
        random.shuffle(bank)
        picked = bank[:3]
    return {"status": "ok", "level": level, "questions": picked}


def evaluate_answer(user_answer, correct_keyword):
    """Tool 4: Evaluator / verifier - checks if answer contains key idea."""
    if not user_answer:
        return {"status": "ok", "correct": False, "score": 0}
    ua = user_answer.lower()
    ck = correct_keyword.lower()
    # accept partial: e.g. "re-try" for "retry", "memories" for "memory"
    aliases = {"observe decide act evaluate adapt": ["observe", "decide", "act", "evaluate", "adapt", "observe decide", "agentic loop"],
               "memory": ["memory", "memory.json", "memories", "state"],
               "retrieve_notes": ["retrieve_notes", "retrieve", "retrieval", "search", "notes", "tools"],
               "retry": ["retry", "re-try", "try again", "recover", "recovery"],
               "plans tools evaluation memory": ["plan", "tool", "evaluat", "memory", "adapt", "workflow", "agent"]}
    accepted = aliases.get(ck, None)
    if accepted is not None:
        correct = any(x in ua for x in accepted)
    else:
        # Dynamic answers: accept if the keyword (or its stem-like prefix) appears
        correct = ck in ua or ck[:4] in ua
    return {"status": "ok", "correct": correct, "score": 100 if correct else 0}


# Simulated external tool to DEMONSTRATE failure + recovery.
_CALL_COUNT = {"web": 0}


def web_search_mock(query, force_fail_first_time=True):
    """
    Tool 5: External web search (simulated).
    First call fails on purpose to show adaptation in demo video.
    Second call succeeds. This proves robustness.
    """
    _CALL_COUNT["web"] += 1
    if force_fail_first_time and _CALL_COUNT["web"] == 1:
        return {"status": "error",
                "message": "Simulated network timeout. Internet / API failed."}
    return {"status": "ok",
            "message": f"Web result for '{query}': Extra example found - "
                       "a study agent retries a failed API once and continues with local notes."}


def reset_mock():
    _CALL_COUNT["web"] = 0
