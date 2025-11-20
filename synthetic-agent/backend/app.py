# backend/app.py
import streamlit as st
from agent import AIMLAgent
from database import get_last_n_turns
import os

st.set_page_config(page_title="AIML Nexus (Streamlit)", layout="centered")

st.title("AIML Nexus — Backend Chat (Streamlit)")
st.write("A minimal chat UI that talks to the AIML Nexus agent (OpenAI/Local HF/fallback).")

# create/get agent (singleton via session_state)
if "agent" not in st.session_state:
    st.session_state.agent = AIMLAgent()

agent = st.session_state.agent

# user id simple input
user_id = st.text_input("User ID", value=os.getenv('USER', 'local-user'), key="user_id")

# show last N turns from DB
with st.expander("Conversation history (last 20)"):
    rows = get_last_n_turns(20)
    if rows:
        for r in rows:
            st.markdown(f"**{r.user_id}**: {r.user_message}")
            st.markdown(f"> {r.reply}")
    else:
        st.write("_No conversation history yet._")

st.markdown("---")
# input area
user_input = st.text_area("Message", value="", height=120, key="user_input")

col1, col2 = st.columns([1, 1])
with col1:
    send = st.button("Send")
with col2:
    clear = st.button("Clear input")

if clear:
    st.session_state.user_input = ""

if send and user_input.strip():
    with st.spinner("AIML Nexus is thinking..."):
        try:
            reply = agent.respond(user_input.strip(), user_id=user_id)
        except Exception as e:
            reply = f"Error generating reply: {e}"

    st.markdown("**You:**")
    st.write(user_input)
    st.markdown("**AIML Nexus:**")
    st.info(reply)

    st.experimental_rerun()