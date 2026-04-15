import requests

API_KEY = "7fbeb87ff692e15b30b0e1abf8364033"

def get_weather(city):

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url, timeout=5)

        print("Weather API Status:", response.status_code)

        if response.status_code != 200:
            return {
                "weather": "Clear",
                "visibility": 10000,
                "wind_speed": 2
            }

        data = response.json()

        return {
            "weather": data["weather"][0]["main"],
            "visibility": data.get("visibility", 10000),
            "wind_speed": data["wind"]["speed"]
        }

    except Exception as e:
        print("Weather API Error:", e)

        # 🔥 fallback (important)
        return {
            "weather": "Clear",
            "visibility": 10000,
            "wind_speed": 2
        }