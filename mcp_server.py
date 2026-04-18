from fastapi import FastAPI
import pandas as pd
import joblib
from pydantic import BaseModel
import boto3
import json
import uuid
import datetime
import os

from services.mcp_engine import mcp_engine

# ----------------------------------
# LOAD MODEL
# ----------------------------------
model = joblib.load("model.pkl")
FEATURES = list(model.feature_names_in_)

app = FastAPI(title="Aviation MCP-style Server (Real-Time)")

# ----------------------------------
# INPUT SCHEMA
# ----------------------------------
class FlightInput(BaseModel):
    origin: str
    hour: int = 12

    Weather_Thunderstorm: int = 0
    Weather_Rain: int = 0
    Weather_Fog: int = 0
    Airport_Traffic_Medium: int = 0
    Airport_Traffic_Low: int = 0


# ----------------------------------
# TOOL 1: PREDICTION
# ----------------------------------
@app.post("/tool/predict-flight-delay")
def predict_flight_delay(input_data: FlightInput):

    data = input_data.dict()

    df = pd.DataFrame([data])
    df = df.reindex(columns=FEATURES, fill_value=0)

    prediction = int(model.predict(df)[0])

    # 🔥 MCP reasoning impact
    try:
        realtime_reasons = mcp_engine(data)

        for reason in realtime_reasons:
            if "weather" in reason.lower():
                prediction += 5
            if "wind" in reason.lower():
                prediction += 3
            if "congestion" in reason.lower():
                prediction += 3

    except Exception as e:
        print("MCP Error:", e)

    # Business rules
    if data.get("Weather_Thunderstorm", 0):
        prediction += 7

    if data.get("Weather_Rain", 0):
        prediction += 3

    if data.get("Weather_Fog", 0):
        prediction += 4

    if data.get("Airport_Traffic_Medium", 0):
        prediction += 3

    if prediction < 0:
        prediction = 0

    # Save result to S3
    bucket_name = os.getenv("S3_BUCKET_NAME", "your-unique-s3-bucket-name")
    try:
        s3 = boto3.client('s3')
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "input_data": data,
            "prediction_minutes": prediction,
            "type": "prediction"
        }
        s3.put_object(
            Bucket=bucket_name,
            Key=f"predictions/{record['id']}.json",
            Body=json.dumps(record)
        )
        print(f"Successfully saved prediction to S3 bucket: {bucket_name}")
    except Exception as e:
        print(f"Failed to save prediction to S3: {e}")

    return {"prediction": prediction}


# ----------------------------------
# TOOL 2: REASONING
# ----------------------------------
@app.post("/tool/delay-reason")
def delay_reason(input_data: FlightInput):

    data = input_data.dict()
    reasons = []

    # 🔥 MCP real-time
    try:
        realtime_reasons = mcp_engine(data)
        reasons.extend(realtime_reasons)

    except Exception as e:
        print("MCP Error:", e)
        reasons.append("⚠️ Unable to fetch real-time weather data")

    # Business fallback
    if data.get("Weather_Thunderstorm", 0):
        reasons.append("Thunderstorm significantly disrupts flight operations")

    if data.get("Weather_Rain", 0):
        reasons.append("Rain slows down runway operations")

    if data.get("Weather_Fog", 0):
        reasons.append("Fog reduces visibility")

    if data.get("Airport_Traffic_Medium", 0):
        reasons.append("Moderate airport traffic can cause delays")

    if data.get("Airport_Traffic_Low", 0):
        reasons.append("Low traffic helps flights stay on time")

    if not reasons:
        reasons.append("Normal operating conditions")

    # Save reasons result to S3
    bucket_name = os.getenv("S3_BUCKET_NAME", "your-unique-s3-bucket-name")
    try:
        s3 = boto3.client('s3')
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "input_data": data,
            "reasons": reasons,
            "type": "reason"
        }
        s3.put_object(
            Bucket=bucket_name,
            Key=f"reasons/{record['id']}.json",
            Body=json.dumps(record)
        )
        print(f"Successfully saved reason to S3 bucket: {bucket_name}")
    except Exception as e:
        print(f"Failed to save reason to S3: {e}")

    return {"reasons": reasons}


# ----------------------------------
# HEALTH CHECK
# ----------------------------------
@app.get("/")
def home():
    return {"message": "Aviation MCP Server Running 🚀"}