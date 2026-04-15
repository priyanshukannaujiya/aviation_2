from services.weather_service import get_weather

def mcp_engine(data):
    reasons = []

    try:
        weather = get_weather(data["origin"])

        if weather["visibility"] < 5000:
            reasons.append("Low visibility due to fog")

        if weather["weather"] in ["Rain", "Thunderstorm"]:
            reasons.append("Bad weather conditions")

        if weather["wind_speed"] > 10:
            reasons.append("High wind speed affecting flights")

    except Exception as e:
        print("Weather Error:", e)
        reasons.append("⚠️ Weather data unavailable")

    hour = data.get("hour", 12)

    if 6 <= hour <= 10 or 17 <= hour <= 22:
        reasons.append("Peak hour airport congestion")

    return reasons