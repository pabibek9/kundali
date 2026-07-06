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

# Country capitals with coordinates for geocoding fallbacks
COUNTRY_CAPITALS = {
    "nepal": (27.7172, 85.3240, "Kathmandu, Nepal"),
    "india": (28.6139, 77.2090, "New Delhi, India"),
    "new zealand": (-41.2865, 174.7762, "Wellington, New Zealand"),
    "nz": (-41.2865, 174.7762, "Wellington, New Zealand"),
    "australia": (-35.2809, 149.1300, "Canberra, Australia"),
    "united kingdom": (51.5074, -0.1278, "London, United Kingdom"),
    "uk": (51.5074, -0.1278, "London, United Kingdom"),
    "great britain": (51.5074, -0.1278, "London, United Kingdom"),
    "united states": (38.9072, -77.0369, "Washington D.C., United States"),
    "usa": (38.9072, -77.0369, "Washington D.C., United States"),
    "us": (38.9072, -77.0369, "Washington D.C., United States"),
    "canada": (45.4215, -75.6972, "Ottawa, Canada"),
    "germany": (52.5200, 13.4050, "Berlin, Germany"),
    "france": (48.8566, 2.3522, "Paris, France"),
    "japan": (35.6762, 139.6503, "Tokyo, Japan"),
    "china": (39.9042, 116.4074, "Beijing, China"),
    "uae": (24.4539, 54.3773, "Abu Dhabi, United Arab Emirates"),
    "united arab emirates": (24.4539, 54.3773, "Abu Dhabi, United Arab Emirates"),
    "dubai": (25.2048, 55.2708, "Dubai, United Arab Emirates"),
    "singapore": (1.3521, 103.8198, "Singapore"),
    "bangladesh": (23.8103, 90.4125, "Dhaka, Bangladesh"),
    "pakistan": (33.6844, 73.0479, "Islamabad, Pakistan"),
    "sri lanka": (6.9271, 79.8612, "Colombo, Sri Lanka"),
    "bhutan": (27.4728, 89.6377, "Thimphu, Bhutan"),
    "maldives": (4.1755, 73.5093, "Male, Maldives"),
    "malaysia": (3.1390, 101.6869, "Kuala Lumpur, Malaysia"),
    "thailand": (13.7563, 100.5018, "Bangkok, Thailand"),
    "qatar": (25.2854, 51.5310, "Doha, Qatar"),
    "saudi arabia": (24.7136, 46.6753, "Riyadh, Saudi Arabia"),
    "kuwait": (29.3759, 47.9774, "Kuwait City, Kuwait"),
    "bahrain": (26.2285, 50.5860, "Manama, Bahrain"),
    "oman": (23.5859, 58.4059, "Muscat, Oman"),
    "netherlands": (52.3676, 4.9041, "Amsterdam, Netherlands"),
    "switzerland": (46.9480, 7.4474, "Bern, Switzerland"),
    "italy": (41.9028, 12.4964, "Rome, Italy"),
    "spain": (40.4168, -3.7038, "Madrid, Spain"),
    "portugal": (38.7223, -9.1393, "Lisbon, Portugal"),
    "russia": (55.7558, 37.6173, "Moscow, Russia"),
    "south korea": (37.5665, 126.9780, "Seoul, South Korea"),
    "brazil": (-15.7975, -47.8919, "Brasilia, Brazil"),
    "south africa": (-25.7479, 28.2293, "Pretoria, South Africa"),
    "turkey": (39.9334, 32.8597, "Ankara, Turkey"),
    "indonesia": (-6.2088, 106.8456, "Jakarta, Indonesia"),
    "philippines": (14.5995, 120.9842, "Manila, Philippines"),
    "vietnam": (21.0285, 105.8542, "Hanoi, Vietnam"),
    "poland": (52.2297, 21.0122, "Warsaw, Poland"),
    "sweden": (59.3293, 18.0686, "Stockholm, Sweden"),
    "norway": (59.9139, 10.7522, "Oslo, Norway"),
    "denmark": (55.6761, 12.5683, "Copenhagen, Denmark"),
    "finland": (60.1699, 24.9384, "Helsinki, Finland"),
    "ireland": (53.3498, -6.2603, "Dublin, Ireland"),
    "austria": (48.2082, 16.3738, "Vienna, Austria"),
    "belgium": (50.8503, 4.3517, "Brussels, Belgium"),
    "greece": (37.9838, 23.7275, "Athens, Greece"),
    "mexico": (19.4326, -99.1332, "Mexico City, Mexico"),
    "argentina": (-34.6037, -58.3816, "Buenos Aires, Argentina"),
    "chile": (-33.4489, -70.6693, "Santiago, Chile"),
    "colombia": (4.7110, -74.0721, "Bogota, Colombia"),
    "egypt": (30.0444, 31.2357, "Cairo, Egypt"),
    "nigeria": (9.0579, 7.4951, "Abuja, Nigeria"),
    "kenya": (-1.2921, 36.8219, "Nairobi, Kenya"),
    "israel": (31.7683, 35.2137, "Jerusalem, Israel"),
    "newzealand": (-41.2865, 174.7762, "Wellington, New Zealand"),
}

def fallback_country_capital(query):
    """
    Looks for a country name or abbreviation in the query and returns the capital's coordinates and name.
    """
    if not query:
        return None
    import re
    q = query.lower().strip()
    
    # 1. Check multi-word country names first
    for country, data in COUNTRY_CAPITALS.items():
        if len(country.split()) > 1 and country in q:
            return data
            
    # 2. Tokenize and check single words / abbreviations
    words = re.findall(r'[a-z0-9]+', q)
    for country, data in COUNTRY_CAPITALS.items():
        if country in words:
            return data
            
    return None

def local_nepal_lookup(query):
    """Try to match a query against known Nepal district/city names resiliently (handles typos like 'okhaldhungha')."""
    import difflib
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
        
        # Fuzzy match to handle common misspellings (e.g. okhaldhungha -> okhaldhunga)
        matches = difflib.get_close_matches(part, NEPAL_DISTRICT_COORDS.keys(), n=1, cutoff=0.75)
        if matches:
            matched_key = matches[0]
            lat, lon = NEPAL_DISTRICT_COORDS[matched_key]
            return lat, lon, f"{matched_key.title()}, Nepal"
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
        
        # If no results found, try country capital fallback
        if not results:
            capital_result = fallback_country_capital(query)
            if capital_result:
                lat, lon, addr = capital_result
                results = [{"address": f"{addr} (Approximate)", "lat": lat, "lon": lon}]
            else:
                # Ultimate fallback to capital of Nepal
                results = [{"address": "Kathmandu, Nepal (Approximate)", "lat": 27.7172, "lon": 85.3240}]
                
        return jsonify(results)
    except Exception as e:
        print(f"Error during location search: {e}")
        return jsonify({"error": "server was unable to process"}), 500

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
            # 1. Check hardcoded Nepal district/city lookup first (instant, no network call)
            nepal_result = local_nepal_lookup(place)
            if nepal_result:
                lat, lon, addr = nepal_result
                if not place_name:
                    place_name = addr
            else:
                # 2. Fall back to external geocoding APIs
                results = resilient_geocode(place)
                if results:
                    lat = results[0]["lat"]
                    lon = results[0]["lon"]
                    if not place_name:
                        place_name = results[0]["address"]
                else:
                    # 3. Fall back to country capital
                    capital_result = fallback_country_capital(place)
                    if capital_result:
                        lat, lon, addr = capital_result
                        if not place_name:
                            place_name = f"{addr} (Approximate)"
                    else:
                        # 4. Ultimate fallback to Kathmandu, Nepal
                        lat, lon, addr = 27.7172, 85.3240, "Kathmandu, Nepal"
                        if not place_name:
                            place_name = "Kathmandu, Nepal (Approximate)"
        except Exception as e:
            print(f"Error resolving location coordinates: {e}")
            # Secure fallback to Kathmandu coordinates
            lat, lon = 27.7172, 85.3240
            if not place_name:
                place_name = "Kathmandu, Nepal (Approximate)"

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
        print(f"Exception during generate_kundali execution: {e}")
        return jsonify({"error": "server was unable to process"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
