import os
import time
from flask import Flask, request, jsonify, render_template
from time_utils import get_timezone_from_coords, get_utc_time
from astrology import calculate_kundali
from report import format_kundali_data
from geopy.geocoders import Nominatim, Photon
from geopy.exc import GeocoderTimedOut
import math

app = Flask(__name__)

# Hardcoded coordinates for all 77 Nepal districts — eliminates external geocoding dependency
NEPAL_DISTRICT_COORDS = {
    "bhojpur": (27.1765, 87.0509), "dhankuta": (26.9842, 87.3444),
    "ilam": (26.9102, 87.9264), "jhapa": (26.6394, 87.8942),
    "khotang": (27.0123, 86.8486), "morang": (26.6683, 87.4609),
    "okhaldhunga": (27.3163, 86.5015), "panchthar": (27.1323, 87.7806),
    "sankhuwasabha": (27.3702, 87.2301), "solukhumbu": (27.7909, 86.6606),
    "sunsari": (26.6556, 87.1699), "taplejung": (27.3519, 87.6709),
    "terhathum": (27.0771, 87.5572), "udayapur": (26.9293, 86.5211),
    "bara": (27.0667, 85.0000), "dhanusha": (26.8065, 85.9266),
    "mahottari": (26.7657, 85.7685), "parsa": (27.0733, 84.8272),
    "rautahat": (27.0030, 85.2814), "saptari": (26.6407, 86.6833),
    "sarlahi": (26.8541, 85.5742), "siraha": (26.6546, 86.2013),
    "bhaktapur": (27.6710, 85.4298), "chitwan": (27.5291, 84.3542),
    "dhading": (27.8717, 84.9317), "dolakha": (27.7776, 86.0726),
    "kathmandu": (27.7172, 85.3240), "kavrepalanchok": (27.5450, 85.5562),
    "lalitpur": (27.6588, 85.3247), "makwanpur": (27.4167, 85.0333),
    "nuwakot": (27.9088, 85.1645), "ramechhap": (27.3272, 86.0884),
    "rasuwa": (28.0833, 85.2833), "sindhuli": (27.2569, 85.9733),
    "sindhupalchok": (27.9530, 85.6839),
    "baglung": (28.2719, 83.5900), "gorkha": (28.3829, 84.6286),
    "kaski": (28.2096, 83.9856), "lamjung": (28.2936, 84.3542),
    "manang": (28.6660, 84.0167), "mustang": (28.9985, 83.8473),
    "myagdi": (28.3667, 83.5000), "nawalpur": (27.8000, 84.1000),
    "parbat": (28.2200, 83.7100), "syangja": (28.0833, 83.8667),
    "tanahun": (27.9394, 84.2273),
    "arghakhanchi": (27.9500, 83.1500), "banke": (28.0500, 81.6000),
    "bardiya": (28.3400, 81.3200), "dang": (27.8600, 82.3000),
    "gulmi": (28.0833, 83.2667), "kapilvastu": (27.5700, 83.0500),
    "parasi": (27.5000, 83.5000), "palpa": (27.8667, 83.5333),
    "pyuthan": (28.1000, 82.8667), "rolpa": (28.3667, 82.6500),
    "rukum east": (28.6000, 82.5500), "rupandehi": (27.5167, 83.4167),
    "dailekh": (28.8500, 81.7167), "dolpa": (29.0000, 82.8667),
    "humla": (29.9700, 81.9000), "jajarkot": (28.7000, 82.2000),
    "jumla": (29.2747, 82.1838), "kalikot": (29.1333, 81.6167),
    "mugu": (29.5000, 82.0833), "rukum west": (28.5833, 82.5000),
    "salyan": (28.3833, 82.1667), "surkhet": (28.5986, 81.6350),
    "achham": (29.0500, 81.2500), "baitadi": (29.5229, 80.4179),
    "bajhang": (29.5400, 81.1900), "bajura": (29.3500, 81.3500),
    "dadeldhura": (29.3000, 80.5833), "darchula": (29.8500, 80.5500),
    "doti": (29.2667, 80.9500), "kailali": (28.7333, 80.5667),
    "kanchanpur": (28.8500, 80.3167),
    # Common city names within Nepal
    "pokhara": (28.2096, 83.9856), "biratnagar": (26.4525, 87.2718),
    "birgunj": (27.0104, 84.8770), "bharatpur": (27.6833, 84.4333),
    "janakpur": (26.7288, 85.9247), "hetauda": (27.4288, 85.0322),
    "dharan": (26.8121, 87.2836), "butwal": (27.7006, 83.4483),
    "nepalgunj": (28.0500, 81.6167), "itahari": (26.6644, 87.2747),
    "damak": (26.6600, 87.6900), "tulsipur": (28.1308, 82.2961),
    "siddharthanagar": (27.5083, 83.4550), "lahan": (26.7167, 86.4833),
    "rajbiraj": (26.5411, 86.7356), "tikapur": (28.5269, 81.1192),
}

def local_nepal_lookup(query):
    """Try to match a query against known Nepal district/city names. Returns (lat, lon, address) or None."""
    q = query.lower().strip()
    # Strip common suffixes like ", nepal", ", province" etc.
    for suffix in [", nepal", " nepal", " district", " municipality"]:
        q = q.replace(suffix, "").strip()
    # Also try stripping province info
    parts = [p.strip() for p in q.split(",")]
    # Try each part from left to right
    for part in parts:
        part = part.strip().lower()
        if part in NEPAL_DISTRICT_COORDS:
            lat, lon = NEPAL_DISTRICT_COORDS[part]
            return lat, lon, f"{part.title()}, Nepal"
    return None


def resilient_geocode(query):
    """
    Geocodes a location query using Photon (Komoot OSM search) as the primary geocoder
    (no rate limits or blocks) and falls back to OSM Nominatim (with email/unique user-agent) if needed.
    """
    formatted_results = []
    
    # 1. Try Photon first (highly resilient, fast, doesn't block Render IPs)
    try:
        geolocator = Photon(user_agent="pabib_kundali_app", timeout=10)
        locations = geolocator.geocode(query, exactly_one=False)
        if locations:
            for loc in locations[:5]:
                formatted_results.append({
                    "address": loc.address,
                    "lat": loc.latitude,
                    "lon": loc.longitude
                })
            return formatted_results
    except Exception as e:
        print(f"Photon geocoding failed: {e}")
        
    # 2. Fallback to OSM Nominatim if Photon fails or returns nothing
    try:
        geolocator = Nominatim(
            user_agent="pabibek_kundali_generator_app_v2",
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
        # Check hardcoded Nepal lookup first (instant)
        nepal_result = local_nepal_lookup(query)
        if nepal_result:
            lat, lon, addr = nepal_result
            return jsonify([{"address": addr, "lat": lat, "lon": lon}])
        # Fall back to external geocoding
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
        # 1. Check hardcoded Nepal district/city lookup first (instant, no network call)
        nepal_result = local_nepal_lookup(place)
        if nepal_result:
            lat, lon, addr = nepal_result
            if not place_name:
                place_name = addr
        else:
            # 2. Fall back to external geocoding APIs
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
