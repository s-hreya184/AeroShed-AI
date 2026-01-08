import streamlit as st
import requests
import json

st.set_page_config(page_title="AeroShed AI Copilot", layout="centered")

st.title("✈️ AeroShed AI – Operational Copilot")
st.caption("Local LLM (Phi-3) for Explainable Crew Scheduling Decisions")

# ---- Runtime analysis from your ML models (mock for now) ----
analysis = {
    "crew_fatigue": {
        "score": 0.78,
        "risk_level": "High",
        "reason": "Extended duty hours and reduced rest"
    },
    "weather_risk": {
        "level": "Moderate",
        "wind_speed": 32,
        "visibility": "Low"
    },
    "schedule_feasibility": {
        "feasible": False,
        "issue": "Crew rest violation"
    },
    "delay_probability": 0.62
}

# ---- Phi-3 call ----
def chat_phi3(user_question, analysis):
    system_prompt = f"""
You are an aviation operational risk explanation assistant.

STRICT RULES:
- Use ONLY the analysis provided below.
- Do NOT invent values, causes, or assumptions.
- Do NOT suggest changes unless explicitly asked.
- If the question cannot be answered using the analysis, say:
  "This question cannot be answered with the available model outputs."

ANALYSIS:
{json.dumps(analysis, indent=2)}

TASK:
Answer the user's question clearly, concisely, and factually.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3",
            "prompt": system_prompt + "\nUSER QUESTION: " + user_question,
            "stream": False
        },
        timeout=60
    )

    return response.json()["response"]

# ---- UI ----
st.markdown("### Ask the AI about the current operational risk")

user_query = st.text_input(
    "Example: Why is this flight considered high risk?"
)

if user_query:
    with st.spinner("Analyzing with Phi-3..."):
        try:
            answer = chat_phi3(user_query, analysis)
            st.success(answer)
        except Exception as e:
            st.error("AI service is not responding. Please ensure Ollama is running.")
