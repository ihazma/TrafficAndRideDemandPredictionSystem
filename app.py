import streamlit as st
import numpy as np
import pandas as pd
import joblib
import pyodbc
from datetime import datetime

# ================================
# PAGE CONFIG
# ================================
st.set_page_config(
    page_title="Traffic & Ride Demand System",
    page_icon="🚦",
    layout="centered"
)

# ================================
# HEADER DESIGN
# ================================
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 40px;
        font-weight: bold;
        color: #1f77b4;
    }
    .sub-title {
        text-align: center;
        font-size: 18px;
        color: gray;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🚦 Traffic & Ride Demand Prediction System</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>AI-powered traffic forecasting for smart mobility planning</div>", unsafe_allow_html=True)

# ================================
# LOAD MODEL
# ================================
model = joblib.load("smart_traffic_demand_system.pkl")

# ================================
# SQL SERVER CONNECTION
# ================================
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=TrafficDemandDB;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

# ================================
# FEATURE ENGINEERING
# ================================
def build_features(hour, weekday, weathersit, temp):

    hr = hour
    mnth = 6
    season = 2
    yr = 1

    is_peak = 1 if (7 <= hr <= 9 or 17 <= hr <= 20) else 0

    hour_sin = np.sin(2 * np.pi * hr / 24)
    hour_cos = np.cos(2 * np.pi * hr / 24)

    month_sin = np.sin(2 * np.pi * mnth / 12)
    month_cos = np.cos(2 * np.pi * mnth / 12)

    is_weekend = 1 if weekday in [0, 6] else 0

    hum = 0.5
    windspeed = 0.2

    return pd.DataFrame([{
        'season': season,
        'yr': yr,
        'mnth': mnth,
        'hr': hr,
        'weekday': weekday,
        'weathersit': weathersit,
        'temp': temp,
        'atemp': temp,
        'hum': hum,
        'windspeed': windspeed,
        'is_peak': is_peak,
        'hour_sin': hour_sin,
        'hour_cos': hour_cos,
        'month_sin': month_sin,
        'month_cos': month_cos,
        'is_weekend': is_weekend
    }])

# ================================
# PREDICTION FUNCTION
# ================================
def predict_traffic(hour, weekday, weathersit, temp):

    input_df = build_features(hour, weekday, weathersit, temp)
    pred = model.predict(input_df)[0]

    if pred < 100:
        return {
            "predicted_demand": round(pred, 2),
            "traffic_level": "LOW",
            "recommended_bikes": 20,
            "alert": "Normal traffic"
        }

    elif pred < 300:
        return {
            "predicted_demand": round(pred, 2),
            "traffic_level": "MEDIUM",
            "recommended_bikes": 50,
            "alert": "Moderate demand"
        }

    else:
        return {
            "predicted_demand": round(pred, 2),
            "traffic_level": "HIGH",
            "recommended_bikes": 100,
            "alert": "SURGE ALERT"
        }

# ================================
# SAVE TO SQL SERVER
# ================================
def save_prediction_sql(hour, weekday, weathersit, temp, result):

    cursor.execute("""
        INSERT INTO Predictions (
            timestamp, hour, weekday, weather, temp,
            demand, traffic_level, recommended_bikes, alert
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(),
        hour,
        weekday,
        weathersit,
        temp,
        result["predicted_demand"],
        result["traffic_level"],
        result["recommended_bikes"],
        result["alert"]
    ))

    conn.commit()

# ================================
# INPUT UI
# ================================
st.markdown("## 📍 Enter Traffic Conditions")

col1, col2 = st.columns(2)

with col1:
    hour = st.slider("Hour of Day", 0, 23, 12)

    weekday_label = st.selectbox(
        "Day",
        ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    )

    weekday_map = {
        "Monday": 1, "Tuesday": 2, "Wednesday": 3,
        "Thursday": 4, "Friday": 5, "Saturday": 6, "Sunday": 0
    }
    weekday = weekday_map[weekday_label]

with col2:
    weather_label = st.selectbox(
        "Weather Condition",
        ["Clear", "Cloudy", "Rainy", "Stormy"]
    )

    weather_map = {
        "Clear": 1,
        "Cloudy": 2,
        "Rainy": 3,
        "Stormy": 4
    }
    weathersit = weather_map[weather_label]

    temp = st.slider("Temperature", 0.0, 1.0, 0.5)

# ================================
# BUTTON + OUTPUT + SQL SAVE
# ================================
st.markdown("---")

if st.button("🚀 Predict Traffic Demand"):

    result = predict_traffic(hour, weekday, weathersit, temp)

    # SAVE TO SQL SERVER
    save_prediction_sql(hour, weekday, weathersit, temp, result)

    st.markdown("## 📊 Prediction Results")

    st.markdown(f"""
    <div style="
        padding: 14px;
        border-radius: 12px;
        background: linear-gradient(135deg,#0f172a,#1e293b);
        color: #38bdf8;
        margin-bottom: 10px;
    ">
    🚲 <b>Predicted Demand:</b> {result["predicted_demand"]}
    </div>
    """, unsafe_allow_html=True)

    if result["traffic_level"] == "LOW":
        color = "#22c55e"
    elif result["traffic_level"] == "MEDIUM":
        color = "#facc15"
    else:
        color = "#ef4444"

    st.markdown(f"""
    <div style="
        padding: 14px;
        border-radius: 12px;
        background: #111827;
        color: {color};
        margin-bottom: 10px;
    ">
    🚦 <b>Traffic Level:</b> {result["traffic_level"]}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="
        padding: 14px;
        border-radius: 12px;
        background: #0b1220;
        color: #e2e8f0;
        margin-bottom: 10px;
    ">
    🚲 <b>Recommended Bikes:</b> {result["recommended_bikes"]}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="
        padding: 14px;
        border-radius: 12px;
        background: #020617;
        color: #f8fafc;
        margin-bottom: 10px;
    ">
    ⚠ <b>Alert:</b> {result["alert"]}
    </div>
    """, unsafe_allow_html=True)

    st.success("Prediction saved to SQL Server successfully!")