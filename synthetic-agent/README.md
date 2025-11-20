# AIML-Nexus-Synthetic-Agent (Backend + Streamlit UI)

This project contains a Streamlit-based backend chat UI and a modular agent
(OpenAI -> Hugging Face -> fallback).

## Quick start

1. Create a Python venv and activate it.
2. pip install -r requirements.txt
3. Set OPENAI_API_KEY if you want OpenAI responses (optional).
4. streamlit run backend/app.py

The Streamlit UI will be available at http://localhost:8501