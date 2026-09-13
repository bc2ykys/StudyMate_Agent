"""StudyMate Agent - app.py. Optional web UI. Needs: pip install streamlit"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

try:
    import streamlit as st
except ImportError:
    print("Streamlit not installed. Run: pip install streamlit")
    print("Or use CLI: python main.py --demo")
    raise SystemExit(1)

from agent import StudyMateAgent
from tools import reset_mock

here = os.path.dirname(__file__)
with open(os.path.join(here, "knowledge_base.txt"), encoding="utf-8") as f:
    KB = f.read()

st.set_page_config(page_title="StudyMate Agentic AI", layout="centered")
st.title("StudyMate - Agentic Study Agent")
st.caption("Goal -> Decision -> Action -> Result -> Adaptation -> Final Outcome")

goal = st.text_input("Your study goal:", "Prepare me for AI agents test")
q1 = st.text_input("Q1: What is the 5-step loop followed by the controller?", "observe decide act evaluate adapt")
q2 = st.text_input("Q2: Which component stores past runs and weak topics?", "")
q3 = st.text_input("Q3: Name one tool the agent can call? (try wrong answer to see adaptation)", "")

if st.button("Run Agent"):
    reset_mock()
    agent = StudyMateAgent(KB)
    # capture prints into trace via agent.log
    result = agent.run(goal, user_answers=[q1, q2, q3], auto_demo=False)
    st.subheader(f"Score: {result['score']}%")
    st.success(result["outcome"])
    if result["weak"]:
        st.warning(f"Weak topics saved to memory: {result['weak']}")
    with st.expander("Full agent trace (for judges)"):
        for line in result["trace"]:
            st.text(line)

st.divider()
st.markdown("**For demo video:** run `python main.py --demo` in terminal and record it. "
            "It shows one failure + recovery automatically.")
