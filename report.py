import json

def get_zodiac_sign_name(index):
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return signs[index]

def format_kundali_data(user_info, kundali_data):
    """
    Formats the raw calculated data into a readable dictionary.
    """
    report = {
        "user_details": user_info,
        "ascendant": {
            "sign": get_zodiac_sign_name(kundali_data["ascendant"]["sign"]),
            "degree": round(kundali_data["ascendant"]["degree"], 2),
            "longitude": round(kundali_data["ascendant"]["longitude"], 2),
            "nakshatra": kundali_data["ascendant"]["nakshatra"],
            "pada": kundali_data["ascendant"]["pada"],
            "syllable": kundali_data["ascendant"]["syllable"]
        },
        "planetary_positions": {},
        "houses": {},
        "aspects": kundali_data["aspects"]
    }
    
    for planet, data in kundali_data["planets"].items():
        report["planetary_positions"][planet] = {
            "sign": get_zodiac_sign_name(data["sign"]),
            "degree": round(data["degree"], 2),
            "is_retrograde": data["is_retrograde"],
            "longitude": round(data["longitude"], 2),
            "nakshatra": data.get("nakshatra", ""),
            "pada": data.get("pada", ""),
            "syllable": data.get("syllable", "")
        }
        
    for house, data in kundali_data["houses"].items():
        report["houses"][house] = {
            "sign": get_zodiac_sign_name(data["sign"]),
            "degree": round(data["degree"], 2),
            "longitude": round(data["longitude"], 2)
        }
        
    return report

def save_report_to_json(report, filename):
    with open(filename, 'w') as f:
        json.dump(report, f, indent=4)
