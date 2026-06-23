import os
import time
import urllib.request
import urllib.parse
import json
from flask import Flask, request, jsonify, render_template
from time_utils import get_timezone_from_coords, get_utc_time
from astrology import calculate_kundali
from report import format_kundali_data
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import math

app = Flask(__name__)

def resilient_geocode(query):
    """
    Geocodes a location query using Open-Meteo as the primary geocoder (no rate limits or blocks)
    and falls back to OSM Nominatim (with email/unique user-agent) if needed.
    """
    # 1. Try Open-Meteo Geocoding first (highly resilient, doesn't block Render IPs)
    results = []
    try:
        # Extract the city/main name (Open-Meteo works best with the core city name)
        search_term = query.split(',')[0].strip()
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(search_term)}&count=5&format=json"
        
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'pabib_kundali_app/1.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            results = data.get("results", [])
    except Exception as e:
        print(f"Open-Meteo geocoding failed: {e}")
        results = []

    formatted_results = []
    if results:
        for item in results:
            address_parts = [item.get("name")]
            if item.get("admin1"):
                address_parts.append(item.get("admin1"))
            if item.get("country"):
                address_parts.append(item.get("country"))
            
            address = ", ".join(address_parts)
            formatted_results.append({
                "address": address,
                "lat": item["latitude"],
                "lon": item["longitude"]
            })
        return formatted_results

    # 2. Fallback to OSM Nominatim if Open-Meteo fails or returns nothing
    try:
        geolocator = Nominatim(
            user_agent="pabibek_kundali_generator_app_v1",
            email="pabibek9@gmail.com",
            timeout=10
        )
        for retry in range(3):
            try:
                locations = geolocator.geocode(query, exactly_one=False, limit=5)
                if locations:
                    for loc in locations:
                        formatted_results.append({
                            "address": loc.address,
                            "lat": loc.latitude,
                            "lon": loc.longitude
                        })
                    return formatted_results
                break
            except GeocoderTimedOut:
                time.sleep(1)
    except Exception as e:
        print(f"Nominatim fallback geocoding failed: {e}")
        
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search_location')
def search_location():
    query = request.args.get('q')
    if not query:
        return jsonify([])
        
    try:
        results = resilient_geocode(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API key from environment variable (falls back to default if not set)
VALID_API_KEY = os.environ.get("API_KEY", "sk-kundali-7f2a8c9d0b5e43")

@app.route('/api/generate', methods=['GET', 'POST'])
def generate_kundali():
    if request.method == 'POST':
        if request.is_json:
            data = request.json
        else:
            data = request.form
    else:
        data = request.args

    # Check API key
    provided_key = (
        request.headers.get("X-API-Key")
        or request.args.get("api_key")
        or (data.get("api_key") if data else None)
    )
    if provided_key != VALID_API_KEY:
        return jsonify({"error": "Unauthorized: Invalid or missing API key"}), 401

    name = data.get('name')
    date_str = data.get('date')
    time_str = data.get('time')
    lat = data.get('lat')
    lon = data.get('lon')
    place = data.get('place') or data.get('location')
    calendar_type = data.get('calendar_type', 'AD')
    place_name = data.get('place_name')

    # Geocoding fallback if lat/lon are not provided but a place/location is
    if (not lat or not lon) and place:
        try:
            results = resilient_geocode(place)
            if results:
                lat = results[0]["lat"]
                lon = results[0]["lon"]
                if not place_name:
                    place_name = results[0]["address"]
            else:
                return jsonify({"error": f"Could not find coordinates for place: '{place}'. Try using the correct English spelling or a nearby major city."}), 400
        except Exception as e:
            return jsonify({"error": f"Geocoding service error: {str(e)}"}), 500

    if not place_name:
        place_name = f"Lat: {lat}, Lon: {lon}" if (lat and lon) else ""

    if not all([name, date_str, time_str, lat, lon]):
        return jsonify({"error": "Missing required fields (must provide either 'lat' and 'lon', or 'place'/'location')"}), 400
        
    try:
        lat = float(lat)
        lon = float(lon)
        tz_name = get_timezone_from_coords(lat, lon)
        if not tz_name:
            return jsonify({"error": "Could not determine timezone for the selected location."}), 400
            
        utc_dt, actual_ad_date = get_utc_time(date_str, time_str, tz_name, calendar_type)
        kundali_data = calculate_kundali(utc_dt, lat, lon)
        
        user_info = {
            "name": name,
            "original_date": date_str,
            "ad_date": actual_ad_date,
            "time_of_birth": time_str,
            "place_of_birth": place_name,
            "latitude": lat,
            "longitude": lon,
            "timezone": tz_name,
            "calendar_type": calendar_type
        }
        
        report = format_kundali_data(user_info, kundali_data)
        
        # Add a custom 'whole_sign_houses' structure for easy North Indian chart rendering
        asc_sign_index = list(["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]).index(report["ascendant"]["sign"])
        chart_houses = {i: {"sign": (asc_sign_index + i - 1) % 12 + 1, "planets": []} for i in range(1, 13)}
        
        nepali_planets = {
            "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल",
            "Mercury": "बुध", "Jupiter": "गुरु", "Venus": "शुक्र",
            "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"
        }
        
        for planet, data in report["planetary_positions"].items():
            p_sign_index = list(["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]).index(data["sign"])
            # Calculate house distance from Ascendant
            house_num = (p_sign_index - asc_sign_index + 12) % 12 + 1
            chart_houses[house_num]["planets"].append(nepali_planets[planet])
            
        report["chart_houses"] = chart_houses
        
        return jsonify(report)
        
    except Exception as e:
        error_msg = str(e)
        if "ephemeris segment only covers" in error_msg:
            return jsonify({
                "error": "The date provided falls outside the supported astronomical calculation range (1899-07-29 to 2053-10-09 AD). If you entered a Nepali (BS) date, please ensure you selected the BS calendar type."
            }), 400
        return jsonify({"error": error_msg}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
