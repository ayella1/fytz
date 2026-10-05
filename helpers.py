import requests
import random
from functools import wraps
from flask import redirect, session

#user data for the app
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

#main weather fetch from nws
def fetch_weather_logic(address):
    # Default to Cambridge, MA
    lat, lon = "42.3736", "-71.1097"
    headers = {"User-Agent": "FytzApp/1.0", "Accept": "application/geo+json"}

    # Geocoding Logic
    if address:
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
            res = requests.get(geo_url, headers=headers, timeout=5).json()
            # Safety check: Nominatim returns a list
            if res and len(res) > 0:
                lat, lon = res[0]["lat"], res[0]["lon"]
        except Exception as e:
            print(f"Geocoding error: {e}")

    #  Weather Logic
    try:
        # Get the forecast grid point
        p_res = requests.get(f"https://api.weather.gov/points/{lat},{lon}", headers=headers, timeout=5).json()
        f_url = p_res["properties"]["forecast"]

        # Get the actual forecast periods
        w_json = requests.get(f_url, headers=headers, timeout=5).json()
        periods = w_json["properties"]["periods"]

        if not periods:
            raise ValueError("No forecast periods found")

        w_data = periods[0]

        # Alerts Logic
        active_alert = None
        try:
            a_res = requests.get(f"https://api.weather.gov/alerts/active?point={lat},{lon}", headers=headers, timeout=5).json()
            # Safety check: Verify features list is not empty
            if a_res.get('features') and len(a_res['features']) > 0:
                active_alert = a_res['features'][0]['properties'].get('headline')
        except:
            pass # Alerts are optional, don't crash if they fail

        return {
            "temp": w_data['temperature'],
            "forecast": w_data['shortForecast'],
            "icon": w_data['icon'] if w_data['icon'] else "https://www.weather.gov/images/forecast/icons/skc.png",
            "alert": active_alert,
            "location": address if address else "Cambridge, MA."
        }

    except Exception as e:
        print(f"Weather API error: {e}. Falling back to Demo Mode.")
        return {
            "temp": 70,
            "forecast": "Sunny (Demo)",
            "icon": "https://www.weather.gov/images/forecast/icons/skc.png",
            "alert": None,
            "location": address or "Cambridge, MA."
        }

