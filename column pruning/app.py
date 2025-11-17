import streamlit as st
import pandas as pd
import os
import json
from pathlib import Path

from column_agent import ColumnPruningAgent   # <-- YOU MUST SAVE YOUR CLASS AS column_agent.py


st.set_page_config(page_title="Column Pruning Agent", layout="wide")

st.title("🧠 Column Pruning Agent (Gemini-powered)")

if not os.getenv("GOOGLE_API_KEY"):
    st.error("❌ GOOGLE_API_KEY is not set. Export it or pass it in Docker.")
    st.stop()

uploaded_file = st.file_uploader("Upload dataset (.csv / .xlsx / parquet)", type=["csv", "xlsx", "xls", "parquet"])

if uploaded_file:
    suffix = uploaded_file.name.lower()

    if suffix.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif suffix.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif suffix.endswith(".parquet"):
        df = pd.read_parquet(uploaded_file)
    else:
        st.error("Unsupported format")
        st.stop()

    st.success(f"Loaded dataset with {df.shape[0]} rows and {df.shape[1]} columns.")
    st.write(df.head())

    query = st.text_input("Enter natural language query:", placeholder="Example: Show average grade by gender")

    mode = st.radio(
        "Select pruning mode",
        ["LLM reasoning", "Offline heuristic"],
        horizontal=True
    )

    run_btn = st.button("🚀 Run Column Pruning")

    if run_btn and query.strip():
        agent = ColumnPruningAgent()

        columns = list(df.columns)

        if mode == "Offline heuristic":
            pruned = agent.prune_offline_simple(query, columns)
            reasons = {c: "Selected by heuristic pattern matching." for c in pruned}
            pruned_out = [c for c in columns if c not in pruned]
        else:
            pruned, reasons, pruned_out = agent.prune_with_reason(query, columns)

        st.subheader("✅ Selected Columns")
        st.write(pruned)

        st.subheader("❌ Removed Columns")
        st.write(pruned_out)

        st.subheader("📊 Efficiency")
        kept = len(pruned)
        removed = len(columns) - kept
        st.write(f"Kept **{kept}/{len(columns)}** columns → Removed **{removed}** ({removed/len(columns)*100:.1f}%)")

        st.subheader("📄 Preview of pruned dataset")
        st.write(df[pruned].head())

        with st.expander("🔎 Full reasoning"):
            st.json(reasons)
