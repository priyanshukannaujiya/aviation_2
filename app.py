import streamlit as st
import requests
import boto3
import json
import pandas as pd
import uuid

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Aviation Delay Intelligence",
    page_icon="✈️",
    layout="wide"
)

# -----------------------------
# S3 CONFIG
# -----------------------------
s3 = boto3.client("s3")
BUCKET_NAME = "aviation-delay-data"   # 🔥 change if needed

def save_to_s3(data):
    file_name = f"inputs/{uuid.uuid4()}.json"

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=file_name,
        Body=json.dumps(data),
        ContentType="application/json"
    )

def load_s3_data():
    data = []

    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix="inputs/"):
        if "Contents" in page:
            for obj in page["Contents"]:
                key = obj["Key"]

                file = s3.get_object(Bucket=BUCKET_NAME, Key=key)
                content = file["Body"].read().decode("utf-8")

                try:
                    data.append(json.loads(content))
                except:
                    pass

    return data

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
<style>
.main {
    background-color: #0e1117;
    color: white;
}
.card {
    background-color: #1c1f26;
    padding: 18px;
    border-radius: 10px;
    margin-bottom: 10px;
    border-left: 5px solid #ff4b4b;
}
.success {
    border-left: 5px solid #00c853;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown("<h1 style='text-align:center;'>✈️ Aviation Delay Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>AI-based flight delay prediction</p>", unsafe_allow_html=True)

st.divider()

# -----------------------------
# INPUT SECTION
# -----------------------------
st.markdown("## 🧾 Flight Details")

col1, col2, col3 = st.columns(3)

with col1:
    origin = st.text_input("📍 Origin City", "Mumbai")

with col2:
    airline = st.selectbox("✈️ Airline", ["IndiGo", "Air India", "SpiceJet", "Vistara"])

with col3:
    hour = st.slider("⏰ Departure Hour", 0, 23, 8)

st.divider()

# -----------------------------
# ADVANCED PARAMETERS
# -----------------------------
st.markdown("## ⚙️ Advanced Parameters")

col4, col5, col6 = st.columns(3)

with col4:
    weather = st.selectbox("🌦 Weather", ["Clear", "Rain", "Fog", "Thunderstorm"])

with col5:
    traffic = st.selectbox("🏢 Airport Traffic", ["Low", "Medium", "High"])

with col6:
    day_type = st.selectbox("📅 Day Type", ["Weekday", "Weekend"])

st.divider()

col7, col8 = st.columns(2)

with col7:
    distance = st.slider("📏 Distance (km)", 100, 3000, 800)

with col8:
    is_peak = st.checkbox("🔥 Peak Hour Flight")

st.divider()

# -----------------------------
# API URL
# -----------------------------
API_URL = "http://13.60.199.165:8000/tool/delay-reason"   # 🔥 update if needed

# -----------------------------
# BUTTON ACTION
# -----------------------------
if st.button("🚀 Analyze Flight Delay"):

    payload = {
        "origin": origin,
        "hour": hour,

        "Weather_Rain": 1 if weather == "Rain" else 0,
        "Weather_Fog": 1 if weather == "Fog" else 0,
        "Weather_Thunderstorm": 1 if weather == "Thunderstorm" else 0,

        "Airport_Traffic_Medium": 1 if traffic == "Medium" else 0,
        "Airport_Traffic_Low": 1 if traffic == "Low" else 0
    }

    with st.spinner("Analyzing flight delay... ✈️"):

        try:
            response = requests.post(API_URL, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
            else:
                st.error(f"❌ Backend error: {response.status_code}")
                st.text(response.text)
                st.stop()

            # -----------------------------
            # SAVE INPUT + OUTPUT TO S3 🔥
            # -----------------------------
            result_data = {
                "input": payload,
                "output": data
            }

            try:
                save_to_s3(result_data)
            except Exception as e:
                st.warning(f"S3 Save Failed: {e}")

            # -----------------------------
            # OUTPUT DISPLAY
            # -----------------------------
            st.markdown("## 📊 Delay Insights")

            if data.get("reasons"):
                for reason in data["reasons"]:
                    st.markdown(f"""
                    <div class="card">
                        ⚠️ {reason}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="card success">
                    ✅ No major delay risks detected
                </div>
                """, unsafe_allow_html=True)

        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend (Is FastAPI running?)")

        except Exception as e:
            st.error("❌ Something went wrong")
            st.write(e)

# -----------------------------
# LOAD S3 DATA
# -----------------------------
st.divider()
st.markdown("## 📂 Past Flight Data")

if st.button("📥 Load Data from S3"):
    with st.spinner("Loading data from S3..."):

        try:
            s3_data = load_s3_data()

            if s3_data:
                df = pd.json_normalize(s3_data)
                st.dataframe(df)
            else:
                st.warning("No data found")

        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------
# FOOTER
# -----------------------------
st.divider()
st.markdown("<p style='text-align:center;'>Built by Silicon Mafias 🚀</p>", unsafe_allow_html=True)
