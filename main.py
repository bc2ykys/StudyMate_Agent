"""StudyMate Agent - main.py. Runnable entry point. No install needed."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from agent import StudyMateAgent
from tools import reset_mock


def load_kb():
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "knowledge_base.txt"), encoding="utf-8") as f:
        return f.read()


def main():
    p = argparse.ArgumentParser(description="StudyMate Agentic AI Demo")
    p.add_argument("--goal", default="Prepare me for AI agents test",
                   help="Study goal")
    p.add_argument("--demo", action="store_true",
                   help="Auto demo mode for video recording (no typing needed)")
    args = p.parse_args()

    reset_mock()  # so failure demo works every run
    agent = StudyMateAgent(load_kb())

    print("=" * 60)
    print("StudyMate - Agentic AI Hackathon Demo (Tech Zephyr 4.0)")
    print("Loop: observe -> decide -> act -> evaluate -> adapt")
    print("=" * 60)

    if args.demo:
        result = agent.run(args.goal, auto_demo=True)
    else:
        result = agent.run(args.goal, auto_demo=False)

    print("=" * 60)
    print("DONE. Final outcome:")
    print(result["outcome"])
    print("=" * 60)


if __name__ == "__main__":
    main()
