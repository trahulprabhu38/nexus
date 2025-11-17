# streamlit_ui.py - Streamlit UI for Intent Agent
import streamlit as st
import requests
import json
from typing import Any, Dict

st.set_page_config(page_title="Nexus Intent UI", layout="centered")

st.title("Nexus — Intent Agent UI")
st.markdown("Enter a query and call the FastAPI intent agent. The UI will show the JSON payload returned by `/predict`.")

# Configure endpoint (editable in UI)
default_api = st.text_input("Intent API URL", value="http://127.0.0.1:8080/predict")
st.write("Using API:", default_api)

with st.form("query_form"):
    text = st.text_area("User query", placeholder="Show my 2nd year marks for Data Structures.", height=120)
    request_id = st.text_input("Request ID (optional)", value="")
    submitted = st.form_submit_button("Send")

if submitted:
    if not text.strip():
        st.warning("Please enter a query.")
    else:
        payload = {
            "request_id": request_id or None,
            "text": text
        }
        st.info("Sending to intent API...")
        try:
            with st.spinner("Contacting intent API..."):
                resp = requests.post(default_api, json=payload, timeout=30)
            if resp.status_code != 200:
                st.error(f"API returned status {resp.status_code}: {resp.text}")
            else:
                data = resp.json()
                st.success("Received response")
                # Pretty JSON
                st.subheader("Raw JSON")
                st.json(data)

                # Friendly view
                st.subheader("Parsed fields")
                intent = data.get("intent", "—")
                conf = data.get("confidence", 0.0)
                st.metric("Intent", f"{intent}", delta=f"confidence: {conf:.2f}")

                entities = data.get("entities", {})
                if entities:
                    st.write("**Entities**")
                    st.table({k: [v] for k, v in entities.items()})

                qd = data.get("query_descriptor", {})
                if qd:
                    st.write("**Query descriptor**")
                    st.json(qd)

                st.subheader("Explanation")
                st.write(data.get("explanation", ""))
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            st.code(f"Try curl:\n\ncurl -X POST {default_api} -H \"Content-Type: application/json\" -d '{{\"request_id\":\"r1\",\"text\":\"{text}\"}}'")

st.sidebar.markdown("**Tips**")
st.sidebar.write("- Make sure the FastAPI server is running on the API URL above.")
st.sidebar.write("- Streamlit runs server-side, so it can call localhost if both services are on same machine.")
