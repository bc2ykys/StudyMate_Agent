"""
StudyMate Agent - agent.py
The AGENT / CONTROLLER.

Loop: observe -> decide -> act -> evaluate -> adapt
Shows: planning, tool use, memory, verification, failure handling.
"""

from tools import (retrieve_notes, make_summary, generate_quiz,
                   evaluate_answer, web_search_mock)
from memory_store import load_memory, update_after_run


class StudyMateAgent:
    def __init__(self, knowledge_text):
        self.knowledge = knowledge_text
        self.log = []  # full trace for demo video

    def _say(self, stage, text):
        line = f"[{stage}] {text}"
        print(line, flush=True)
        self.log.append(line)

    def run(self, goal, user_answers=None, auto_demo=False):
        """
        goal: e.g. 'Prepare me for AI agents test'
        user_answers: list of 3 answers for quiz, or None for interactive.
        auto_demo: if True, uses scripted answers (1 wrong on purpose)
                   to show adaptation + failure recovery.
        Returns dict with final outcome.
        """
        self.log = []
        mem = load_memory()
        self._say("GOAL", goal)
        self._say("MEMORY", f"Past runs={mem.get('runs',0)}, "
                            f"Weak topics={mem.get('weak_topics',[])}")

        # ---- STEP 1: OBSERVE + PLAN ----
        plan = ["1. Retrieve notes", "2. Summarize",
                "3. Try web enrichment", "4. Quiz + evaluate",
                "5. Adapt if weak, else finish"]
        self._say("PLAN", "Agent plan: " + " -> ".join(plan))

        # ---- STEP 2: DECIDE + ACT (retrieval) ----
        self._say("DECISION", "Query is about exam prep, so I will call retrieve_notes first.")
        ret = retrieve_notes(goal, self.knowledge)
        self._say("ACTION", "Called tool: retrieve_notes")
        self._say("RESULT", ret["message"])
        if ret["status"] != "ok":
            # Failure handling path 1: bad query
            self._say("ADAPT", "Retrieval failed. Retrying with broader query 'agent tools memory'.")
            ret = retrieve_notes("agent tools memory planning", self.knowledge)
            self._say("RESULT", "Retry: " + ret["message"])
        for c in ret.get("chunks", []):
            self._say("EVIDENCE", c)

        # ---- STEP 3: SUMMARIZE ----
        summ = make_summary(ret.get("chunks", []))
        self._say("ACTION", "Called tool: make_summary")
        print(summ.get("summary", ""), flush=True)
        self.log.append(summ.get("summary", ""))

        # ---- STEP 4: EXTERNAL TOOL with FAILURE + RECOVERY (for video) ----
        self._say("DECISION", "Trying external web enrichment for extra example.")
        web = web_search_mock(goal, force_fail_first_time=True)
        self._say("ACTION", "Called tool: web_search")
        if web["status"] != "ok":
            self._say("FAILURE", web["message"])
            self._say("ADAPT", "Web failed. I will NOT stop. Retrying once, then continue with local notes only.")
            web2 = web_search_mock(goal, force_fail_first_time=True)
            if web2["status"] == "ok":
                self._say("RECOVERY", "Retry succeeded: " + web2["message"])
            else:
                self._say("RECOVERY", "Web still down. Continuing with local knowledge. System is robust.")
        else:
            self._say("RESULT", web["message"])

        # ---- STEP 5: QUIZ + EVALUATE ----
        quiz = generate_quiz(ret.get("chunks", []), level="easy")
        questions = quiz["questions"]
        self._say("ACTION", f"Called tool: generate_quiz (level=easy, {len(questions)} Qs)")

        answers = []
        if auto_demo:
            # Scripted: Q1 correct, Q2 WRONG on purpose, Q3 correct.
            # This shows adaptation in demo video.
            # Build answers dynamically so they match whatever quiz was generated.
            answers = []
            for i, q in enumerate(questions):
                if i == 1:
                    # Intentionally wrong answer for Q2
                    answers.append("chatbot")
                else:
                    # Correct answer taken from the question itself
                    answers.append(q["a"])
            self._say("DEMO", "Auto-demo answers used (Q2 is intentionally wrong to show adaptation).")
        elif user_answers and len(user_answers) >= len(questions):
            answers = user_answers
        else:
            print("\n--- QUIZ: type your answers ---", flush=True)
            for i, q in enumerate(questions):
                try:
                    a = input(f"Q{i+1}. {q['q']} > ")
                except EOFError:
                    a = ""
                answers.append(a)

        score = 0
        weak = []
        for i, q in enumerate(questions):
            ans = answers[i] if i < len(answers) else ""
            ev = evaluate_answer(ans, q["a"])
            ok = ev["correct"]
            self._say("EVALUATE", f"Q{i+1}: you said '{ans}' | expected idea '{q['a']}' -> "
                                  + ("CORRECT" if ok else "WRONG"))
            if ok:
                score += 1
            else:
                weak.append(q["topic"])

        percent = int(score / len(questions) * 100)
        self._say("INTERMEDIATE", f"Quiz score: {score}/{len(questions)} = {percent}%")

        # ---- STEP 6: ADAPT ----
        if percent < 100:
            self._say("ADAPT", f"Weak topics found: {weak}. Re-planning with REMEDIAL path.")
            remedial = generate_quiz(ret.get("chunks", []), level="remedial")
            self._say("ACTION", "Remedial notes: Revise controller loop, memory in memory.json, tools list. "
                                "Tip: Loop=observe-decide-act-evaluate-adapt, Store=memory.json, Fail=retry then continue local.")
            self._say("ACTION", f"Remedial quiz generated ({len(remedial['questions'])} easy Qs) for next round.")
            outcome = (f"GOAL PARTIALLY MET. Score {percent}%. Agent adapted: saved weak topics {weak} "
                       "to memory and gave remedial plan. Next session will focus on these first.")
        else:
            outcome = (f"GOAL FULLY MET. Score {percent}%. No weak topics. "
                       "Agent saved success to memory.")

        mem2 = update_after_run(goal, percent, weak)
        self._say("MEMORY", f"Memory updated. Total runs now {mem2['runs']}.")
        self._say("FINAL", outcome)

        return {"goal": goal, "score": percent, "weak": weak,
                "outcome": outcome, "trace": self.log}
