================================================================
StudyMate - Autonomous Learning Planner Agent | README
Track 2: Education | Problem Statement 3: Autonomous Learning Planner
Tech Zephyr 4.0 - Agentic AI Hackathon | IIT Bhubaneswar
================================================================

WHAT IS THIS?
----------------------------------------------------------------
StudyMate is a submission for Problem Statement 3 (Autonomous
Learning Planner) under Track 2: Education.

It is an agentic AI system that works toward a student's
learning goal under changing performance and resource
constraints. You give it a GOAL, it plans, retrieves notes,
summarizes, dynamically generates a quiz from those notes,
checks answers, detects weak topics, adapts with a remedial
path, saves progress to memory for the next session, and
handles tool failures gracefully.

It proves agentic behavior because a simple chatbot cannot do
multi-step plan + tool calls + evaluation + retry + memory.

QUICK RUN (no install, 30 seconds):
----------------------------------------------------------------
1. Install Python 3.10 or above.
2. Open terminal in this folder.
3. Run demo mode (best for video):
     python main.py --demo
4. Run interactive mode (type your own answers):
     python main.py --goal "Prepare me for AI agents test"
5. Optional web UI:
     pip install streamlit
     streamlit run app.py

FILES IN THIS REPO:
----------------------------------------------------------------
main.py                  - Entry point (CLI). Use --demo for video.
agent.py                 - Agent/controller. The observe-decide-act-
                           evaluate-adapt loop lives here.
tools.py                 - 5 tools: retrieve_notes, make_summary,
                           generate_quiz (DYNAMIC from notes),
                           evaluate_answer, web_search.
memory_store.py          - Memory/state in memory.json.
knowledge_base.txt       - Sample study notes (AI agents basics).
app.py                   - Optional Streamlit web UI.
test_studymate.py        - 27 unit tests. Run: python -m unittest test_studymate -v
package.ps1              - PowerShell: cleans pycache, resets memory, zips folder.
requirements.txt         - Only streamlit is optional. Core = zero deps.
.env.example             - Template. Never commit real keys.
README.txt               - This file.
ARCHITECTURE.txt         - Full architecture documentation.
Problem_Solution_Brief.txt - Stage 1 item A.
Architecture_Diagram.txt - Stage 1 item B (ASCII diagram).
Demo_Video_Script.txt    - Stage 1 item D script (3-5 min).
HOW_TO_RUN.txt           - Stage 1 item E (for judges).
memory.json              - Agent long-term memory (auto-updated).

ENVIRONMENT CONFIG:
----------------------------------------------------------------
No key needed. Works fully offline.
If you later add Gemini/OpenAI, copy .env.example to .env
and put your key there. Never push .env to GitHub.

DEPENDENCIES:
----------------------------------------------------------------
Core: Python standard library only.
Optional UI: pip install -r requirements.txt

ARCHITECTURE IN 5 LINES:
----------------------------------------------------------------
User Goal -> Agent plans -> Tools (retrieval, quiz, web,
evaluator) -> Verifier checks score -> If weak, adapt with
remedial path + update memory.json -> Final outcome.

LICENSE / USE:
----------------------------------------------------------------
Built for Agentic AI Hackathon Round 1 submission.
Free to use and modify for the hackathon.
