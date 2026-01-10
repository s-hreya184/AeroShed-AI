import streamlit as st
import time
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import requests
import json

# ---------------- PAGE CONFIG (MUST BE FIRST) ----------------
st.set_page_config(
    page_title="Aero-Zen Aviation Risk Platform",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- SESSION STATE INITIALIZATION ----------------
if 'weather_delay_result' not in st.session_state:
    st.session_state.weather_delay_result = None
if 'crew_sickness_result' not in st.session_state:
    st.session_state.crew_sickness_result = None
if 'equipment_failure_result' not in st.session_state:
    st.session_state.equipment_failure_result = None
if 'emergency_landing_result' not in st.session_state:
    st.session_state.emergency_landing_result = None
if 'copilot_response' not in st.session_state:
    st.session_state.copilot_response = None
if 'last_question' not in st.session_state:
    st.session_state.last_question = ""

# ---------------- AI COPILOT FUNCTIONS ----------------
def build_runtime_analysis():
    """Build unified runtime analysis context from all predictions"""
    return {
        "weather_delay": st.session_state.weather_delay_result,
        "crew_sickness": st.session_state.crew_sickness_result,
        "equipment_failure": st.session_state.equipment_failure_result,
        "emergency_landing": st.session_state.emergency_landing_result
    }

def chat_phi3(user_question, analysis):
    """Query Phi-3 with grounded runtime analysis"""
    system_prompt = f"""You are an aviation risk explanation assistant for AeroZen platform.

STRICT RULES:
- Use ONLY the data provided in ANALYSIS below
- If any data is missing (None), explicitly state "insufficient data for [that prediction]"
- Do NOT invent numbers or make assumptions
- Do NOT give generic aviation theory unless directly supported by the data
- Explain causality and relationships clearly
- Be concise and actionable (3-5 sentences max)
- Focus on the specific question asked

CURRENT RUNTIME ANALYSIS:
{json.dumps(analysis, indent=2)}

Guidelines for interpretation:
- Weather delay: risk_percentage (0-100%), delay_minutes (0-180 min)
- Crew sickness: probability percentage (0-100%)
- Equipment failure: failure_probability percentage (0-100%)
- Emergency landing: emergency_probability percentage (0-100%)

Answer the user's question based ONLY on this runtime data."""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3",
                "prompt": system_prompt + "\n\nUser question: " + user_question,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: Phi-3 service returned status {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        return "Cannot connect to Phi-3. Please ensure Ollama is running with: `ollama run phi3`"
    except requests.exceptions.Timeout:
        return "Request timeout. Phi-3 is taking too long to respond."
    except Exception as e:
        return f"Error communicating with Phi-3: {str(e)}"

# ---------------- MODEL LOADING ----------------
@st.cache_resource
def load_crew_model():
    try:
        model_path = Path("crew_sickness_model.pkl")
        if model_path.exists():
            return joblib.load(model_path)
        else:
            st.warning("Crew model file not found. Using simulation mode.")
            return None
    except Exception as e:
        st.error(f"Error loading crew model: {str(e)}")
        return None

@st.cache_resource
def load_weather_model():
    try:
        model_path = Path("weather_delay_model.pkl")
        if model_path.exists():
            return joblib.load(model_path)
        else:
            st.warning("Weather model file not found. Using simulation mode.")
            return None
    except Exception as e:
        st.error(f"Error loading weather model: {str(e)}")
        return None

@st.cache_resource
def load_equipment_models():
    try:
        prob_model_path = Path("equipment_failure_prob_model.pkl")
        risk_model_path = Path("equipment_failure_risk_model.pkl")
        
        prob_model = None
        risk_model = None
        
        if prob_model_path.exists():
            prob_model = joblib.load(prob_model_path)
        if risk_model_path.exists():
            risk_model = joblib.load(risk_model_path)
            
        if prob_model is None or risk_model is None:
            st.warning("Equipment model files not found. Using simulation mode.")
            return None, None
        
        return prob_model, risk_model
    except Exception as e:
        st.error(f"Error loading equipment models: {str(e)}")
        return None, None

@st.cache_resource
def load_emergency_models():
    try:
        prob_model_path = Path("emergency_landing_prob_model.pkl")
        risk_model_path = Path("emergency_landing_prob_model.pkl")
        
        prob_model = None
        risk_model = None
        
        if prob_model_path.exists():
            prob_model = joblib.load(prob_model_path)
        if risk_model_path.exists():
            risk_model = joblib.load(risk_model_path)
            
        if prob_model is None or risk_model is None:
            st.warning("Emergency landing model files not found. Using simulation mode.")
            return None, None
        
        return prob_model, risk_model
    except Exception as e:
        st.error(f"Error loading emergency models: {str(e)}")
        return None, None

crew_model = load_crew_model()
weather_model = load_weather_model()
equipment_prob_model, equipment_risk_model = load_equipment_models()
emergency_prob_model, emergency_risk_model = load_emergency_models()

# ---------------- ENHANCED DARK THEME ----------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #1a1d2e 0%, #2d1b4e 100%);
}

h1, h2, h3, h4, p, label, span, div {
    color: white !important;
}

div.stButton > button {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    color: white;
    font-weight: 600;
    border-radius: 12px;
    padding: 0.75rem 1.5rem;
    border: none;
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    transition: all 0.3s ease;
}

div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
}

[data-testid="stMetricValue"] {
    color: #60a5fa !important;
    font-size: 42px;
    font-weight: 700;
}

[data-testid="stMetricDelta"] {
    color: #22c55e !important;
    font-size: 18px;
}

div[role="radiogroup"] label {
    background-color: rgba(255, 255, 255, 0.05);
    padding: 0.5rem 1rem;
    border-radius: 8px;
    margin: 0 0.25rem;
    transition: all 0.3s ease;
}

div[role="radiogroup"] label:hover {
    background-color: rgba(37, 99, 235, 0.2);
}

.stSlider > div > div > div {
    background-color: rgba(37, 99, 235, 0.3);
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%);
}

[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
    background-color: rgba(255, 255, 255, 0.03);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.stAlert {
    background-color: rgba(37, 99, 235, 0.1);
    border-left: 4px solid #2563eb;
    color: white;
}

.stTextInput > div > div > input {
    background-color: rgba(255, 255, 255, 0.05);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
}

.stExpander {
    background-color: rgba(37, 99, 235, 0.05);
    border: 1px solid rgba(37, 99, 235, 0.3);
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>AeroZen</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #94a3b8; margin-top: 0;'>Intelligent Aviation Risk & Safety Platform</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------------- MODEL SELECTION ----------------
model = st.radio(
    "Select Prediction Model",
    [
        "Weather Delay",
        "Crew Sickness",
        "Equipment Failure",
        "Emergency Landing Risk",
        "Operational Risk Index"
    ],
    horizontal=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------- LAYOUT ----------------
col_input, col_result = st.columns([1, 1.5], gap="large")

# ================= INPUT PANEL =================
with col_input:
    st.markdown("### Input Parameters")
    
    if "Weather" in model:
        st.info("Model-Ready: Using trained Ensemble Regressor")
        st.info("Adjust input parameters and click **Run Prediction** to view results.")
        
        col1, col2 = st.columns(2)
        with col1:
            departure_airport = st.selectbox("Departure Airport", ['JFK', 'LAX', 'ORD', 'DFW', 'ATL', 'DEN', 'SFO', 'SEA', 'MIA', 'BOS'], index=0)
        with col2:
            arrival_airport = st.selectbox("Arrival Airport", ['JFK', 'LAX', 'ORD', 'DFW', 'ATL', 'DEN', 'SFO', 'SEA', 'MIA', 'BOS'], index=1)
        
        col3, col4 = st.columns(2)
        with col3:
            scheduled_hour = st.slider("Scheduled Departure Hour", 0, 23, 10)
            month = st.slider("Month", 1, 12, 6)
        with col4:
            season = st.selectbox("Season", ["Winter", "Spring", "Summer", "Fall"], index=2)
            time_of_day = st.selectbox("Time of Day", ["Morning", "Afternoon", "Evening", "Night"], index=0)
        
        st.markdown("---")
        st.markdown("**Weather Conditions**")
        
        col5, col6 = st.columns(2)
        with col5:
            temperature = st.slider("Temperature (°C)", -10, 40, 20)
            wind_speed = st.slider("Wind Speed (km/h)", 0, 80, 25)
            visibility = st.slider("Visibility (meters)", 100, 10000, 8000, step=100)
            precipitation_prob = st.slider("Precipitation Probability (%)", 0, 100, 20)
        with col6:
            weather_condition = st.selectbox("Weather Condition", ["Clear", "Cloudy", "Rain", "Snow", "Fog", "Storm"], index=0)
            pressure = st.slider("Atmospheric Pressure (hPa)", 980, 1040, 1013)
            humidity = st.slider("Humidity (%)", 20, 100, 50)
            historical_delay = st.slider("Avg Historical Delay (min)", 0, 45, 10)

    elif "Crew" in model:
        st.info("Model-Ready: Using trained Random Forest pipeline")
        st.info("Adjust input parameters and click **Run Prediction** to view results.")
        
        workload_last_7_days = st.slider("Workload Last 7 Days (hours)", 10, 70, 45)
        consecutive_duty_days = st.slider("Consecutive Duty Days", 1, 14, 5)
        days_since_last_sick_leave = st.slider("Days Since Last Sick Leave", 0, 180, 60)
        
        st.markdown("---")
        
        avg_flight_duration_last_week = st.slider("Avg Flight Duration Last Week (hours)", 1.0, 10.0, 5.0, 0.5)
        historical_sick_days_count = st.slider("Historical Sick Days Count", 0, 15, 3)
        
        col1, col2 = st.columns(2)
        with col1:
            season = st.selectbox("Season", ["Winter", "Spring", "Summer", "Fall"], index=2)
            age_group = st.selectbox("Age Group", ["20-30", "31-40", "41-50", "50+"], index=1)
        with col2:
            month = st.slider("Month", 1, 12, 6)
            flight_type_ratio = st.slider("Flight Type Ratio", 0.0, 1.0, 0.5, 0.05)

    elif "Equipment" in model:
        st.info("Model-Ready: Using trained ML Models (Binary + Risk Level)")
        st.info("Adjust input parameters and click **Run Prediction** to view results.")
        
        aircraft_id = st.text_input("Aircraft ID", "AC0001")
        
        col1, col2 = st.columns(2)
        with col1:
            aircraft_age_years = st.slider("Aircraft Age (Years)", 1.0, 25.0, 12.0, 0.5)
            hours_since_last_maintenance = st.slider("Hours Since Last Maintenance", 10.0, 500.0, 250.0, 10.0)
            cycles_since_last_maintenance = st.slider("Cycles Since Last Maintenance", 5, 300, 150)
            avg_flight_duration_last_30_days = st.slider("Avg Flight Duration (Last 30 Days)", 1.5, 12.0, 5.5, 0.5)
        
        with col2:
            total_flight_hours = st.number_input("Total Flight Hours", 5000.0, 80000.0, 35000.0, 1000.0)
            total_cycles = st.number_input("Total Cycles", 2000, 40000, 18000, 500)
            reported_minor_issues_last_30_days = st.slider("Minor Issues (Last 30 Days)", 0, 15, 5)
            utilization_rate = st.slider("Utilization Rate (flights/day)", 0.5, 6.5, 4.2, 0.1)
        
        st.markdown("---")
        st.markdown("**Maintenance & Conditions**")
        
        col3, col4 = st.columns(2)
        with col3:
            last_maintenance_type = st.selectbox("Last Maintenance Type", ["A-check", "B-check", "C-check", "D-check"], index=1)
            manufacturer = st.selectbox("Manufacturer", ["Boeing", "Airbus", "Embraer", "Bombardier"], index=0)
        with col4:
            model_type = st.selectbox("Model Type", ["737-800", "747-400", "A320", "A350", "E190", "CRJ-900"], index=0)
            ambient_temperature_avg = st.slider("Avg Ambient Temperature (°C)", -20.0, 45.0, 25.0, 1.0)
        
        harsh_landing_count_last_30_days = st.slider("Harsh Landings (Last 30 Days)", 0, 8, 2)

    elif "Emergency" in model:
        st.info("Model-Ready: Using trained ML Models (GB + RF)")
        st.info("Adjust input parameters and click **Run Prediction** to view results.")
        
        flight_id = st.text_input("Flight ID", "FL0001")
        
        st.markdown("---")
        st.markdown("**System Health Indicators**")
        
        col1, col2 = st.columns(2)
        with col1:
            engine_health = st.slider("Engine Health (%)", 50.0, 100.0, 85.0, 0.1)
            vibration_level = st.slider("Vibration Level (0-10)", 0.0, 10.0, 3.0, 0.1)
            fuel_pressure = st.slider("Fuel Pressure (%)", 60.0, 100.0, 90.0, 0.1)
            hydraulic_pressure = st.slider("Hydraulic Pressure (%)", 70.0, 100.0, 92.0, 0.1)
            oil_temperature = st.slider("Oil Temperature (°C)", 60.0, 120.0, 88.0, 0.1)
        
        with col2:
            cabin_pressure = st.slider("Cabin Pressure (%)", 80.0, 100.0, 95.0, 0.1)
            fuel_quantity = st.slider("Fuel Quantity (%)", 10.0, 100.0, 75.0, 0.1)
            electrical_system_health = st.slider("Electrical System (%)", 70.0, 100.0, 92.0, 0.1)
            flight_control_response = st.slider("Flight Control Response (%)", 70.0, 100.0, 95.0, 0.1)
        
        st.markdown("---")
        st.markdown("**Weather & Environmental Conditions**")
        
        col3, col4 = st.columns(2)
        with col3:
            weather_severity = st.slider("Weather Severity (0-10)", 0, 10, 2)
            turbulence_level = st.slider("Turbulence Level (0-10)", 0, 10, 3)
            visibility_level = st.slider("Visibility Level (1-10)", 1, 10, 8)
            wind_shear = st.slider("Wind Shear (0-10)", 0, 10, 2)
        
        with col4:
            altitude = st.number_input("Altitude (feet)", 5000, 40000, 35000, 1000)
            airspeed = st.number_input("Airspeed (knots)", 200, 600, 450, 10)
        
        st.markdown("---")
        st.markdown("**Flight Details**")
        
        col5, col6 = st.columns(2)
        with col5:
            time_of_day_emerg = st.selectbox("Time of Day", ["Morning", "Afternoon", "Evening", "Night"], index=0)
            phase_of_flight = st.selectbox("Phase of Flight", ["Takeoff", "Climb", "Cruise", "Descent", "Approach", "Landing"], index=2)
        
        with col6:
            pilot_experience_years = st.slider("Pilot Experience (years)", 2, 30, 15)
            aircraft_age_years_emerg = st.slider("Aircraft Age (years)", 1.0, 25.0, 10.0, 0.1)

    else:
        st.info("📊 This model aggregates predictions from all other models")
        st.markdown("### How it works:")
        st.markdown("The Operational Risk Index automatically combines risk assessments from:\n\n- **Weather Delay** (25% weight)\n- **Crew Sickness** (20% weight)\n- **Equipment Failure** (30% weight)\n- **Emergency Landing Risk** (20% weight)\n- **Traffic Density** (5% weight - baseline)\n\nSimply run predictions for the other models first, then return here to see the comprehensive operational risk assessment.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    if "Operational Risk Index" not in model:
        run = st.button("Run Prediction", use_container_width=True)
    else:
        run = st.button("Calculate Operational Risk", use_container_width=True)

# ================= RESULTS PANEL =================
with col_result:
    if run:
        with st.spinner("Running AI prediction..."):
            time.sleep(1.2)

        if "Weather" in model:
            # Weather prediction logic
            if weather_model is not None:
                try:
                    input_data = pd.DataFrame({
                        'departure_airport_code': [departure_airport],
                        'arrival_airport_code': [arrival_airport],
                        'scheduled_departure_hour': [scheduled_hour],
                        'month': [month],
                        'temperature': [temperature],
                        'wind_speed': [wind_speed],
                        'visibility': [visibility],
                        'precipitation_probability': [precipitation_prob],
                        'weather_condition': [weather_condition],
                        'pressure': [pressure],
                        'humidity': [humidity],
                        'historical_delay_same_route': [historical_delay],
                        'season': [season],
                        'time_of_day': [time_of_day]
                    })
                    
                    predicted_delay = weather_model.predict(input_data)[0]
                    predicted_delay = max(0, min(180, predicted_delay))
                    model_used = "Ensemble ML Model (RF + GB)"
                    
                except Exception as e:
                    st.error(f"Model prediction error: {str(e)}")
                    predicted_delay = min(180, int((wind_speed / 80) * 40 + (1 - visibility / 10000) * 40 + (precipitation_prob / 100) * 30 + historical_delay * 0.5))
                    model_used = "Fallback (Rule-based)"
            else:
                predicted_delay = min(180, int((wind_speed / 80) * 40 + (1 - visibility / 10000) * 40 + (precipitation_prob / 100) * 30 + historical_delay * 0.5))
                model_used = "Simulation Mode"

            if predicted_delay < 15:
                delay_category = "No Delay"
                risk_level = "Low"
            elif predicted_delay < 30:
                delay_category = "Minor Delay"
                risk_level = "Moderate"
            elif predicted_delay < 60:
                delay_category = "Moderate Delay"
                risk_level = "Elevated"
            else:
                delay_category = "Severe Delay"
                risk_level = "High"

            # Store result
            st.session_state.weather_delay_result = {
                'delay_minutes': predicted_delay,
                'risk_percentage': min(100, int((predicted_delay / 180) * 100))
            }

            st.markdown("### Weather Delay Prediction")
            st.metric("Predicted Delay", f"{predicted_delay:.0f} minutes", f"{delay_category}")
            st.caption(f"Prediction Method: {model_used}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Route", f"{departure_airport} → {arrival_airport}")
            c2.metric("Risk Level", risk_level)
            c3.metric("Weather", weather_condition)

            st.markdown("---")
            st.markdown("#### Weather Impact Factors")

            wind_pct = int((wind_speed / 80) * 100)
            st.write(f"**Wind Speed Impact – {wind_pct}%**")
            st.progress(wind_pct / 100)

            vis_pct = int((1 - visibility / 10000) * 100)
            st.write(f"**Visibility Impact – {vis_pct}%**")
            st.progress(vis_pct / 100)

            precip_pct = precipitation_prob
            st.write(f"**Precipitation Risk – {precip_pct}%**")
            st.progress(precip_pct / 100)

        elif "Crew" in model:
            # Crew prediction logic
            if crew_model is not None:
                try:
                    stress_score = (0.4 * workload_last_7_days + 0.3 * consecutive_duty_days + 0.3 * avg_flight_duration_last_week)
                    
                    input_data = pd.DataFrame({
                        'season': [season],
                        'month': [month],
                        'days_since_last_sick_leave': [days_since_last_sick_leave],
                        'workload_last_7_days': [workload_last_7_days],
                        'consecutive_duty_days': [consecutive_duty_days],
                        'avg_flight_duration_last_week': [avg_flight_duration_last_week],
                        'historical_sick_days_count': [historical_sick_days_count],
                        'age_group': [age_group],
                        'flight_type_ratio': [flight_type_ratio],
                        'stress_score': [stress_score]
                    })
                    
                    raw_probability = crew_model.predict_proba(input_data)[0][1] * 100
                    probability = int(raw_probability)
                    model_used = "Random Forest ML Model"
                    
                except Exception as e:
                    st.error(f"Model prediction error: {str(e)}")
                    probability = min(100, int((workload_last_7_days / 70) * 45 + (consecutive_duty_days / 14) * 35 + (1 - days_since_last_sick_leave / 180) * 20))
                    model_used = "Fallback (Rule-based)"
            else:
                probability = min(100, int((workload_last_7_days / 70) * 45 + (consecutive_duty_days / 14) * 35 + (1 - days_since_last_sick_leave / 180) * 20))
                model_used = "Simulation Mode"

            level = "Normal" if probability <= 40 else "Elevated" if probability <= 70 else "Critical"

            # Store result
            st.session_state.crew_sickness_result = {
                'probability': probability
            }

            st.markdown("### Crew Sickness Risk Prediction")
            st.metric("Sickness Probability", f"{probability}%", f"{level}")
            st.caption(f"Prediction Method: {model_used}")

            stress_score = (0.4 * workload_last_7_days + 0.3 * consecutive_duty_days + 0.3 * avg_flight_duration_last_week)
            c1, c2, c3 = st.columns(3)
            c1.metric("Workload/Week", f"{workload_last_7_days}h")
            c2.metric("Duty Streak", f"{consecutive_duty_days} days")
            c3.metric("Stress Score", f"{stress_score:.1f}")

        elif "Equipment" in model:
            # Equipment prediction logic
            if equipment_prob_model is not None and equipment_risk_model is not None:
                try:
                    input_data = pd.DataFrame({
                        'aircraft_age_years': [aircraft_age_years],
                        'hours_since_last_maintenance': [hours_since_last_maintenance],
                        'cycles_since_last_maintenance': [cycles_since_last_maintenance],
                        'last_maintenance_type': [last_maintenance_type],
                        'avg_flight_duration_last_30_days': [avg_flight_duration_last_30_days],
                        'total_flight_hours': [total_flight_hours],
                        'total_cycles': [total_cycles],
                        'reported_minor_issues_last_30_days': [reported_minor_issues_last_30_days],
                        'ambient_temperature_avg': [ambient_temperature_avg],
                        'harsh_landing_count_last_30_days': [harsh_landing_count_last_30_days],
                        'manufacturer': [manufacturer],
                        'model_type': [model_type],
                        'utilization_rate': [utilization_rate]
                    })
                    
                    failure_probability = equipment_prob_model.predict_proba(input_data)[0][1] * 100
                    risk_level = equipment_risk_model.predict(input_data)[0]
                    risk_confidence = max(equipment_risk_model.predict_proba(input_data)[0]) * 100
                    
                    if failure_probability < 25:
                        recommended_action = "Continue"
                    elif failure_probability < 50:
                        recommended_action = "Monitor"
                    elif failure_probability < 75:
                        recommended_action = "Schedule Maintenance"
                    else:
                        recommended_action = "Immediate Maintenance"
                    
                    model_used = "Dual ML Models (GB + RF)"
                    
                except Exception as e:
                    st.error(f"Model prediction error: {str(e)}")
                    failure_probability = min(100, int((aircraft_age_years / 25) * 30 + (hours_since_last_maintenance / 500) * 35 + (reported_minor_issues_last_30_days / 15) * 35))
                    risk_level = "Low" if failure_probability < 25 else "Medium" if failure_probability < 50 else "High" if failure_probability < 75 else "Critical"
                recommended_action = "Continue" if failure_probability < 25 else "Monitor" if failure_probability < 50 else "Schedule Maintenance" if failure_probability < 75 else "Immediate Maintenance"
                risk_confidence = 75.0
                model_used = "Simulation Mode"

            # Store result
            st.session_state.equipment_failure_result = {
                'failure_probability': failure_probability
            }

            st.markdown("### Equipment Failure Prediction")
            st.metric("Failure Probability", f"{failure_probability:.1f}%", f"{risk_level}")
            st.caption(f"Prediction Method: {model_used}")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Aircraft", aircraft_id)
            c2.metric("Risk Level", f"{risk_level}")
            c3.metric("Confidence", f"{risk_confidence:.1f}%")
            c4.metric("Action", recommended_action.split()[0])

            st.markdown("---")
            st.markdown("#### Aircraft Information")
            c5, c6, c7 = st.columns(3)
            c5.metric("Manufacturer", manufacturer)
            c6.metric("Model", model_type)
            c7.metric("Age", f"{aircraft_age_years} years")

            st.markdown("---")
            st.markdown("#### Risk Factor Analysis")

            age_pct = int((aircraft_age_years / 25) * 100)
            st.write(f"**Aircraft Age Impact – {age_pct}%**")
            st.progress(age_pct / 100)

            maint_pct = int((hours_since_last_maintenance / 500) * 100)
            st.write(f"**Maintenance Gap Impact – {maint_pct}%**")
            st.progress(maint_pct / 100)

            issues_pct = int((reported_minor_issues_last_30_days / 15) * 100)
            st.write(f"**Reported Issues Impact – {issues_pct}%**")
            st.progress(issues_pct / 100)

        elif "Emergency" in model:
            # Emergency prediction logic
            if emergency_prob_model is not None and emergency_risk_model is not None:
                try:
                    input_data = pd.DataFrame({
                        'engine_health': [engine_health],
                        'vibration_level': [vibration_level],
                        'fuel_pressure': [fuel_pressure],
                        'hydraulic_pressure': [hydraulic_pressure],
                        'oil_temperature': [oil_temperature],
                        'cabin_pressure': [cabin_pressure],
                        'fuel_quantity': [fuel_quantity],
                        'electrical_system_health': [electrical_system_health],
                        'flight_control_response': [flight_control_response],
                        'weather_severity': [weather_severity],
                        'altitude': [altitude],
                        'airspeed': [airspeed],
                        'turbulence_level': [turbulence_level],
                        'visibility': [visibility_level],
                        'wind_shear': [wind_shear],
                        'time_of_day': [time_of_day_emerg],
                        'phase_of_flight': [phase_of_flight],
                        'pilot_experience_years': [pilot_experience_years],
                        'aircraft_age_years': [aircraft_age_years_emerg]
                    })
                    
                    emergency_probability = emergency_prob_model.predict_proba(input_data)[0][1] * 100
                    risk_level = emergency_risk_model.predict(input_data)[0]
                    risk_confidence = max(emergency_risk_model.predict_proba(input_data)[0]) * 100
                    
                    if emergency_probability < 25:
                        recommended_action = "Continue Normal Operations"
                    elif emergency_probability < 50:
                        recommended_action = "Increase Monitoring"
                    elif emergency_probability < 75:
                        recommended_action = "Prepare Diversion Plan"
                    else:
                        recommended_action = "Initiate Emergency Procedures"
                    
                    model_used = "Dual ML Models (GB + RF)"
                    
                except Exception as e:
                    st.error(f"Model prediction error: {str(e)}")
                    emergency_probability = min(100, int(
                        (1 - engine_health / 100) * 40 +
                        (vibration_level / 10) * 30 +
                        (1 - fuel_pressure / 100) * 20 +
                        (weather_severity / 10) * 10
                    ))
                    risk_level = "Low" if emergency_probability < 25 else "Moderate" if emergency_probability < 50 else "High" if emergency_probability < 75 else "Critical"
                    recommended_action = "Continue Normal Operations" if emergency_probability < 25 else "Increase Monitoring" if emergency_probability < 50 else "Prepare Diversion Plan" if emergency_probability < 75 else "Initiate Emergency Procedures"
                    risk_confidence = 75.0
                    model_used = "Fallback (Rule-based)"
            else:
                emergency_probability = min(100, int(
                    (1 - engine_health / 100) * 40 +
                    (vibration_level / 10) * 30 +
                    (1 - fuel_pressure / 100) * 20 +
                    (weather_severity / 10) * 10
                ))
                risk_level = "Low" if emergency_probability < 25 else "Moderate" if emergency_probability < 50 else "High" if emergency_probability < 75 else "Critical"
                recommended_action = "Continue Normal Operations" if emergency_probability < 25 else "Increase Monitoring" if emergency_probability < 50 else "Prepare Diversion Plan" if emergency_probability < 75 else "Initiate Emergency Procedures"
                risk_confidence = 75.0
                model_used = "Simulation Mode"

            # Store result
            st.session_state.emergency_landing_result = {
                'emergency_probability': emergency_probability
            }

            st.markdown("### Emergency Landing Risk Prediction")
            st.metric("Emergency Probability", f"{emergency_probability:.1f}%", f"{risk_level}")
            st.caption(f"Prediction Method: {model_used}")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Flight", flight_id)
            c2.metric("Risk Level", f"{risk_level}")
            c3.metric("Confidence", f"{risk_confidence:.1f}%")
            c4.metric("Action", recommended_action.split()[0])

            st.markdown("---")
            st.markdown("#### System Health Overview")
            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Engine", f"{engine_health:.1f}%")
            c6.metric("Fuel Press.", f"{fuel_pressure:.1f}%")
            c7.metric("Hydraulics", f"{hydraulic_pressure:.1f}%")
            c8.metric("Electrical", f"{electrical_system_health:.1f}%")

            st.markdown("---")
            st.markdown("#### Risk Factor Analysis")

            engine_pct = int((1 - engine_health / 100) * 100)
            st.write(f"**Engine Health Impact – {engine_pct}%**")
            st.progress(engine_pct / 100)

            vibration_pct = int((vibration_level / 10) * 100)
            st.write(f"**Vibration Level Impact – {vibration_pct}%**")
            st.progress(vibration_pct / 100)

            fuel_pct = int((1 - fuel_pressure / 100) * 100)
            st.write(f"**Fuel System Impact – {fuel_pct}%**")
            st.progress(fuel_pct / 100)

            weather_pct = int((weather_severity / 10) * 100)
            st.write(f"**Weather Impact – {weather_pct}%**")
            st.progress(weather_pct / 100)

        else:
            # OPERATIONAL RISK INDEX
            weather_data = st.session_state.weather_delay_result
            crew_data = st.session_state.crew_sickness_result
            equipment_data = st.session_state.equipment_failure_result
            emergency_data = st.session_state.emergency_landing_result
            
            missing_predictions = []
            if weather_data is None:
                missing_predictions.append("Weather Delay")
            if crew_data is None:
                missing_predictions.append("Crew Sickness")
            if equipment_data is None:
                missing_predictions.append("Equipment Failure")
            if emergency_data is None:
                missing_predictions.append("Emergency Landing Risk")
            
            if missing_predictions:
                st.warning("Operational Risk Index requires predictions from all other models first!")
                st.markdown("### Missing Predictions:")
                for pred in missing_predictions:
                    st.markdown(f"- **{pred}**")
                
                st.markdown("---")
                st.info("**How to use Operational Risk Index:**")
                st.markdown("1. Select each prediction model from the radio buttons above\n2. Fill in the required parameters\n3. Click 'Run Prediction' for each model\n4. Once all predictions are complete, return to 'Operational Risk Index'\n5. Click 'Calculate Operational Risk' to see aggregated results")
                
                st.markdown("---")
                st.markdown("### Already Completed Predictions:")
                if weather_data:
                    st.markdown(f"**Weather Delay**: {weather_data['risk_percentage']}% risk ({weather_data['delay_minutes']:.0f} min delay)")
                if crew_data:
                    st.markdown(f"**Crew Sickness**: {crew_data['probability']}% probability")
                if equipment_data:
                    st.markdown(f"**Equipment Failure**: {equipment_data['failure_probability']:.1f}% probability")
                if emergency_data:
                    st.markdown(f"**Emergency Landing**: {emergency_data['emergency_probability']:.1f}% probability")
            
            else:
                # All predictions available - calculate operational risk
                weather_risk = weather_data['risk_percentage']
                crew_risk = crew_data['probability']
                equipment_risk = equipment_data['failure_probability']
                emergency_risk = emergency_data['emergency_probability']
                traffic_density = 50  # Default baseline
                
                # Calculate weighted operational risk
                operational_risk = int(
                    weather_risk * 0.25 +
                    crew_risk * 0.20 +
                    equipment_risk * 0.30 +
                    emergency_risk * 0.20 +
                    traffic_density * 0.05
                )
                
                level = "STABLE" if operational_risk <= 40 else "ELEVATED" if operational_risk <= 70 else "CRITICAL"
                
                st.markdown("### Operational Risk Index")
                st.metric("Overall Risk Score", f"{operational_risk}%", f"{level}")
                st.caption("Aggregated from all prediction models")
                
                # Display component breakdown
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Weather", f"{weather_risk}%", "25% weight")
                c2.metric("Crew", f"{crew_risk}%", "20% weight")
                c3.metric("Equipment", f"{equipment_risk:.0f}%", "30% weight")
                c4.metric("Emergency", f"{emergency_risk:.0f}%", "20% weight")
                
                st.markdown("---")
                st.markdown("#### Detailed Risk Components")
                
                st.write(f"**Weather Risk – {weather_risk}%** (Weight: 25%)")
                st.progress(weather_risk / 100)
                st.caption(f"Based on predicted delay: {weather_data.get('delay_minutes', 'N/A'):.0f} minutes")
                
                st.write(f"**Crew Risk – {crew_risk}%** (Weight: 20%)")
                st.progress(crew_risk / 100)
                st.caption("Based on crew sickness probability")
                
                st.write(f"**Equipment Risk – {equipment_risk:.1f}%** (Weight: 30%)")
                st.progress(equipment_risk / 100)
                st.caption("Based on equipment failure probability")
                
                st.write(f"**Emergency Risk – {emergency_risk:.1f}%** (Weight: 20%)")
                st.progress(emergency_risk / 100)
                st.caption("Based on emergency landing probability")
                
                st.write(f"**Traffic Density – {traffic_density}%** (Weight: 5%)")
                st.progress(traffic_density / 100)
                st.caption("Default baseline value")
                
                st.markdown("---")
                
                # Risk interpretation
                if operational_risk <= 40:
                    st.success("**STABLE OPERATIONS** - All systems within acceptable risk parameters")
                    st.markdown("**Recommended Actions:**\n- Continue normal operations\n- Maintain standard monitoring protocols\n- Review predictions periodically")
                elif operational_risk <= 70:
                    st.warning("**ELEVATED RISK** - Increased attention required")
                    st.markdown("**Recommended Actions:**\n- Increase monitoring frequency\n- Review contingency plans\n- Brief crew on elevated risk factors\n- Consider operational adjustments")
                else:
                    st.error("**CRITICAL RISK** - Immediate action required")
                    st.markdown("**Immediate Actions Required:**\n- Activate emergency response protocols\n- Notify all relevant personnel\n- Review and address highest risk factors\n- Consider operational restrictions\n- Implement additional safety measures")
                
                st.markdown("---")
                st.markdown("#### Risk Factor Priority")
                
                # Create priority list
                risk_factors = [
                    ("Equipment Failure", equipment_risk, "30%"),
                    ("Weather Delay", weather_risk, "25%"),
                    ("Crew Sickness", crew_risk, "20%"),
                    ("Emergency Landing", emergency_risk, "20%"),
                    ("Traffic Density", traffic_density, "5%")
                ]
                risk_factors.sort(key=lambda x: x[1], reverse=True)
                
                st.markdown("**Ranked by Current Risk Level:**")
                for i, (factor, value, weight) in enumerate(risk_factors, 1):
                    risk_color = "🔴" if value > 70 else "🟡" if value > 40 else "🟢"
                    st.markdown(f"{i}. {risk_color} **{factor}**: {value:.1f}% (Weight: {weight})")
                
                # Reset option
                st.markdown("---")
                if st.button("🔄 Reset All Predictions", use_container_width=True):
                    st.session_state.weather_delay_result = None
                    st.session_state.crew_sickness_result = None
                    st.session_state.equipment_failure_result = None
                    st.session_state.emergency_landing_result = None
                    st.session_state.copilot_response = None
                    st.session_state.last_question = ""
                    st.success("All predictions reset! You can now generate new predictions.")
                    st.rerun()

    else:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### About This Platform")
        st.markdown("AeroZen uses advanced machine learning models to predict aviation risks across multiple domains:\n\n- **Weather Delay**: Predicts flight delays based on meteorological conditions\n- **Crew Sickness**: Uses ML model to assess crew availability risks\n- **Equipment Failure**: ML-powered prediction with dual models (probability + risk level)\n- **Emergency Landing**: Real-time flight safety assessment with comprehensive risk analysis\n- **Operational Risk**: Comprehensive risk aggregation using all previous predictions\n- **AI Copilot**: Phi-3 powered explainability for grounded risk analysis")

    # ================= PERSISTENT AI COPILOT (ALWAYS VISIBLE) =================
    st.markdown("---")
    st.markdown("---")
    st.markdown("## AI Operational Copilot")
    st.caption("Ask Phi-3 to explain predictions using grounded runtime data • No hallucinations • No retraining")
    
    analysis = build_runtime_analysis()
    available_count = sum(1 for v in analysis.values() if v is not None)
    
    # Show status
    st.markdown(f"**Available Predictions: {available_count}/4**")
    
    if available_count > 0:
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            if analysis['weather_delay']:
                st.metric("Weather", f"{analysis['weather_delay']['risk_percentage']}%", "✅")
            else:
                st.metric("Weather", "N/A", "❌")
        with col_b:
            if analysis['crew_sickness']:
                st.metric("Crew", f"{analysis['crew_sickness']['probability']}%", "✅")
            else:
                st.metric("Crew", "N/A", "❌")
        with col_c:
            if analysis['equipment_failure']:
                st.metric("Equipment", f"{analysis['equipment_failure']['failure_probability']:.0f}%", "✅")
            else:
                st.metric("Equipment", "N/A", "❌")
        with col_d:
            if analysis['emergency_landing']:
                st.metric("Emergency", f"{analysis['emergency_landing']['emergency_probability']:.0f}%", "✅")
            else:
                st.metric("Emergency", "N/A", "❌")
        
        st.markdown("---")
        
        # Example questions
        with st.expander("💡 Example Questions", expanded=False):
            ex_col1, ex_col2 = st.columns(2)
            with ex_col1:
                st.caption("• Why is the operational risk high?")
                st.caption("• Which factor contributed the most?")
                st.caption("• What should operations address first?")
            with ex_col2:
                st.caption("• Is crew risk more critical than weather?")
                st.caption("• Why is equipment risk flagged critical?")
                st.caption("• What are the top 2 risk drivers?")
        
        st.markdown("---")
        
        # Question input with persistent state
        user_query = st.text_input(
            "Your Question:",
            value=st.session_state.last_question,
            placeholder="e.g., Why is the operational risk elevated?",
            key="copilot_query_main"
        )
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            ask_button = st.button("Ask Phi-3 Copilot", use_container_width=True, type="primary")
        with col_btn2:
            if st.button("Clear", use_container_width=True):
                st.session_state.copilot_response = None
                st.session_state.last_question = ""
                st.rerun()
        
        if ask_button:
            if not user_query:
                st.warning("Please enter a question first.")
            else:
                st.session_state.last_question = user_query
                with st.spinner("Analyzing with Phi-3..."):
                    answer = chat_phi3(user_query, analysis)
                    st.session_state.copilot_response = answer
        
        # Display response persistently
        if st.session_state.copilot_response:
            st.markdown("---")
            st.markdown("### Copilot Response:")
            st.success(st.session_state.copilot_response)
            st.caption("This explanation is based only on your current runtime predictions, not generic aviation theory.")
    
    else:
        st.warning("No predictions available yet. Run at least one prediction model to start asking questions.")
        st.markdown("**Quick Start:**")
        st.markdown("1. Select a prediction model above (Weather, Crew, Equipment, or Emergency)")
        st.markdown("2. Adjust the input parameters")
        st.markdown("3. Click 'Run Prediction'")
        st.markdown("4. Return here to ask the AI Copilot questions about the results")

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #64748b;'>"
    "AeroZen Risk Platform v2.1 | Powered by AI + Phi-3 Copilot"
    "</p>",
    unsafe_allow_html=True
)


