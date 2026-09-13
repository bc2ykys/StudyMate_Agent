"""
test_studymate.py - Unit tests for StudyMate Agent.

Run:  python -m pytest test_studymate.py -v
  or: python test_studymate.py
"""

import os
import sys
import json
import unittest

# Ensure imports resolve from the same directory as this file.
sys.path.insert(0, os.path.dirname(__file__))

from tools import (retrieve_notes, make_summary, generate_quiz,
                   evaluate_answer, web_search_mock, reset_mock,
                   _parse_kb_questions)
from memory_store import load_memory, save_memory, update_after_run, MEMORY_FILE
from agent import StudyMateAgent


# ------------------------------------------------------------------
# Sample knowledge text used across tests
# ------------------------------------------------------------------
SAMPLE_KB = """\
AI AGENTS - TECH STUDY NOTES
=======================

1. An AI agent is a goal-driven system that plans steps, calls tools, checks results, and adapts until the full goal is done.
2. The controller follows observe -> decide -> act -> evaluate -> adapt loop instead of answering once like a normal chatbot.
3. Tools are functions the agent can call such as retrieve_notes for search, make_summary for notes, quiz generator, and web search.
4. Memory stores past runs, weak topics, and history in memory.json so the next session starts smarter and more personal.
5. Planning means breaking a goal into 5 steps and branching: if retrieval fails retry broader, if web fails retry then continue local.
"""


class TestRetrieveNotes(unittest.TestCase):
    """Tests for the retrieve_notes tool."""

    def test_keyword_match(self):
        result = retrieve_notes("agent tools", SAMPLE_KB)
        self.assertEqual(result["status"], "ok")
        self.assertGreater(len(result["chunks"]), 0)

    def test_empty_query(self):
        result = retrieve_notes("", SAMPLE_KB)
        self.assertEqual(result["status"], "empty")
        self.assertEqual(result["chunks"], [])

    def test_stop_words_only(self):
        result = retrieve_notes("what is the", SAMPLE_KB)
        self.assertEqual(result["status"], "empty")

    def test_no_match(self):
        result = retrieve_notes("xyzzyplugh", SAMPLE_KB)
        # should either return not_found or fallback with generic chunks
        self.assertIn(result["status"], ("not_found", "ok"))

    def test_fallback_minimum_three_chunks(self):
        """Even a weak match should return at least 3 chunks via fallback."""
        result = retrieve_notes("planning", SAMPLE_KB)
        if result["status"] == "ok":
            self.assertGreaterEqual(len(result["chunks"]), 3)


class TestMakeSummary(unittest.TestCase):
    """Tests for the make_summary tool."""

    def test_normal_input(self):
        chunks = ["Line one is about agents.", "Line two about tools."]
        result = make_summary(chunks)
        self.assertEqual(result["status"], "ok")
        self.assertIn("KEY POINTS", result["summary"])

    def test_empty_input(self):
        result = make_summary([])
        self.assertEqual(result["status"], "error")

    def test_long_chunk_is_truncated(self):
        long_line = "A" * 200
        result = make_summary([long_line])
        self.assertIn("...", result["summary"])


class TestDynamicQuizGenerator(unittest.TestCase):
    """Tests for the dynamic quiz generator and its fallback."""

    def _kb_chunks(self):
        """Return the numbered lines from SAMPLE_KB."""
        return [l.strip() for l in SAMPLE_KB.split("\n")
                if l.strip() and l.strip()[0].isdigit()]

    def test_dynamic_generates_questions(self):
        chunks = self._kb_chunks()
        qs = _parse_kb_questions(chunks)
        self.assertGreaterEqual(len(qs), 3, "Should generate >= 3 dynamic Qs from 5 KB lines")
        for q in qs:
            self.assertIn("______", q["q"])
            self.assertTrue(len(q["a"]) > 0)

    def test_generate_quiz_uses_dynamic(self):
        chunks = self._kb_chunks()
        result = generate_quiz(chunks, level="easy")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["questions"]), 3)

    def test_fallback_on_bad_input(self):
        result = generate_quiz(["short", "tiny"], level="easy")
        self.assertEqual(result["status"], "ok")
        # should fall back to static bank
        self.assertEqual(len(result["questions"]), 3)

    def test_remedial_level(self):
        chunks = self._kb_chunks()
        result = generate_quiz(chunks, level="remedial")
        self.assertEqual(len(result["questions"]), 2)


class TestEvaluateAnswer(unittest.TestCase):
    """Tests for the evaluate_answer tool."""

    def test_correct_static(self):
        result = evaluate_answer("memory", "memory")
        self.assertTrue(result["correct"])

    def test_wrong_answer(self):
        result = evaluate_answer("banana", "memory")
        self.assertFalse(result["correct"])

    def test_empty_answer(self):
        result = evaluate_answer("", "memory")
        self.assertFalse(result["correct"])

    def test_alias_match(self):
        result = evaluate_answer("I think we should retry", "retry")
        self.assertTrue(result["correct"])

    def test_dynamic_keyword_match(self):
        """Dynamic KB answer (not in alias map) should match via substring."""
        result = evaluate_answer("the agent is goal-driven", "agent")
        self.assertTrue(result["correct"])

    def test_dynamic_stem_match(self):
        """First 4 chars of the keyword should also match."""
        result = evaluate_answer("I said cont", "controller")
        self.assertTrue(result["correct"])


class TestWebSearchMock(unittest.TestCase):
    """Tests for the simulated web search tool."""

    def test_first_call_fails(self):
        reset_mock()
        result = web_search_mock("test", force_fail_first_time=True)
        self.assertEqual(result["status"], "error")

    def test_second_call_succeeds(self):
        reset_mock()
        web_search_mock("test", force_fail_first_time=True)
        result = web_search_mock("test", force_fail_first_time=True)
        self.assertEqual(result["status"], "ok")

    def test_no_forced_fail(self):
        reset_mock()
        result = web_search_mock("test", force_fail_first_time=False)
        self.assertEqual(result["status"], "ok")


class TestMemoryStore(unittest.TestCase):
    """Tests for memory_store.py."""

    def setUp(self):
        """Save existing memory so we can restore it after tests."""
        self._backup = None
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                self._backup = f.read()

    def tearDown(self):
        """Restore original memory."""
        if self._backup is not None:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                f.write(self._backup)
        else:
            # reset to clean
            save_memory({"runs": 0, "weak_topics": [], "history": []})

    def test_load_clean(self):
        save_memory({"runs": 0, "weak_topics": [], "history": []})
        mem = load_memory()
        self.assertEqual(mem["runs"], 0)

    def test_update_increments_runs(self):
        save_memory({"runs": 0, "weak_topics": [], "history": []})
        mem = update_after_run("test goal", 66, ["memory"])
        self.assertEqual(mem["runs"], 1)
        self.assertIn("memory", mem["weak_topics"])

    def test_history_capped_at_20(self):
        save_memory({"runs": 0, "weak_topics": [], "history": []})
        for i in range(25):
            update_after_run(f"goal {i}", 50, [])
        mem = load_memory()
        self.assertLessEqual(len(mem["history"]), 20)


class TestAgentEndToEnd(unittest.TestCase):
    """Integration test: run the full agent in demo mode."""

    def setUp(self):
        self._backup = None
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                self._backup = f.read()
        save_memory({"runs": 0, "weak_topics": [], "history": []})

    def tearDown(self):
        if self._backup is not None:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                f.write(self._backup)
        else:
            save_memory({"runs": 0, "weak_topics": [], "history": []})

    def test_demo_run_completes(self):
        reset_mock()
        agent = StudyMateAgent(SAMPLE_KB)
        result = agent.run("Prepare me for AI agents test", auto_demo=True)
        self.assertIn("score", result)
        self.assertIn("outcome", result)
        self.assertIsInstance(result["trace"], list)
        self.assertGreater(len(result["trace"]), 5)

    def test_score_is_integer(self):
        reset_mock()
        agent = StudyMateAgent(SAMPLE_KB)
        result = agent.run("Prepare me for AI agents test", auto_demo=True)
        self.assertIsInstance(result["score"], int)

    def test_memory_updated_after_run(self):
        reset_mock()
        agent = StudyMateAgent(SAMPLE_KB)
        agent.run("Prepare me for AI agents test", auto_demo=True)
        mem = load_memory()
        self.assertEqual(mem["runs"], 1)


if __name__ == "__main__":
    unittest.main()
