import json

def get_zodiac_sign_name(index):
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return signs[index]

SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}

def format_kundali_data(user_info, kundali_data):
    """
    Formats the raw calculated data into a comprehensive readable dictionary.
    """
    report = {
        "user_details": user_info,
        "ascendant": {
            "sign": get_zodiac_sign_name(kundali_data["ascendant"]["sign"]),
            "sign_lord": SIGN_LORDS[get_zodiac_sign_name(kundali_data["ascendant"]["sign"])],
            "degree": round(kundali_data["ascendant"]["degree"], 4),
            "longitude": round(kundali_data["ascendant"]["longitude"], 4),
            "nakshatra": kundali_data["ascendant"]["nakshatra"],
            "nakshatra_lord": kundali_data["ascendant"].get("nakshatra_lord", ""),
            "pada": kundali_data["ascendant"]["pada"],
            "syllable": kundali_data["ascendant"]["syllable"]
        },
        "planetary_positions": {},
        "houses": {},
        "aspects": kundali_data["aspects"],
        "dasha": kundali_data.get("dasha", {})
    }
    
    for planet, data in kundali_data["planets"].items():
        sign_name = get_zodiac_sign_name(data["sign"])
        report["planetary_positions"][planet] = {
            "sign": sign_name,
            "sign_lord": SIGN_LORDS[sign_name],
            "degree": round(data["degree"], 4),
            "is_retrograde": data["is_retrograde"],
            "dignity": data.get("dignity", "neutral"),
            "longitude": round(data["longitude"], 4),
            "nakshatra": data.get("nakshatra", ""),
            "nakshatra_lord": data.get("nakshatra_lord", ""),
            "pada": data.get("pada", ""),
            "syllable": data.get("syllable", "")
        }
        
    for house, data in kundali_data["houses"].items():
        sign_name = get_zodiac_sign_name(data["sign"])
        report["houses"][house] = {
            "sign": sign_name,
            "sign_lord": SIGN_LORDS[sign_name],
            "degree": round(data["degree"], 4),
            "longitude": round(data["longitude"], 4)
        }
        
    return report

def save_report_to_json(report, filename):
    with open(filename, 'w') as f:
        json.dump(report, f, indent=4)
