import math
from skyfield.api import load, Topos
from datetime import datetime, timedelta

# Preload skyfield ephemeris (DE421 is accurate from 1899 to 2053)
try:
    eph = load('de421.bsp')
except:
    pass

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", 
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

SYLLABLES = [
    # 1. Ashwini
    "Chu", "Che", "Cho", "La",
    # 2. Bharani
    "Li", "Lu", "Le", "Lo",
    # 3. Krittika
    "A", "I", "U", "E",
    # 4. Rohini
    "O", "Va", "Vi", "Vu",
    # 5. Mrigashira
    "Ve", "Vo", "Ka", "Ki",
    # 6. Ardra
    "Ku", "Gha", "Ng", "Chha",
    # 7. Punarvasu
    "Ke", "Ko", "Ha", "Hi",
    # 8. Pushya
    "Hu", "He", "Ho", "Da",
    # 9. Ashlesha
    "Di", "Du", "De", "Do",
    # 10. Magha
    "Ma", "Mi", "Mu", "Me",
    # 11. Purva Phalguni
    "Mo", "Ta", "Ti", "Tu",
    # 12. Uttara Phalguni
    "Te", "To", "Pa", "Pi",
    # 13. Hasta
    "Pu", "Sha", "Na", "Tha",
    # 14. Chitra
    "Pe", "Po", "Ra", "Ri",
    # 15. Swati
    "Ru", "Re", "Ro", "Ta",
    # 16. Vishakha
    "Ti", "Tu", "Te", "To",
    # 17. Anuradha
    "Na", "Ni", "Nu", "Ne",
    # 18. Jyeshtha (Pada 4 is Yaa)
    "No", "Ya", "Yi", "Yaa",
    # 19. Mula
    "Ye", "Yo", "Ba", "Bi",
    # 20. Purva Ashadha
    "Bu", "Dha", "Bha", "Dha",
    # 21. Uttara Ashadha
    "Be", "Bo", "Ja", "Ji",
    # 22. Shravana
    "Ju", "Je", "Jo", "Gha",
    # 23. Dhanishta
    "Ga", "Gi", "Gu", "Ge",
    # 24. Shatabhisha
    "Go", "Sa", "Si", "Su",
    # 25. Purva Bhadrapada
    "Se", "So", "Da", "Di",
    # 26. Uttara Bhadrapada
    "Du", "Tha", "Jha", "Na",
    # 27. Revati
    "De", "Do", "Cha", "Chi"
]

# Nakshatra lords for Vimshottari Dasha (in order)
DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
TOTAL_DASHA_YEARS = 120  # Total Vimshottari cycle = 120 years

# Planet exaltation, debilitation, and own signs (sign index 0-11)
PLANET_DIGNITY = {
    "Sun":     {"exalted": 0, "debilitated": 6, "own": [4]},           # Exalted Aries, Debilitated Libra, Own Leo
    "Moon":    {"exalted": 1, "debilitated": 7, "own": [3]},           # Exalted Taurus, Debilitated Scorpio, Own Cancer
    "Mars":    {"exalted": 9, "debilitated": 3, "own": [0, 7]},        # Exalted Capricorn, Debilitated Cancer, Own Aries+Scorpio
    "Mercury": {"exalted": 5, "debilitated": 11, "own": [2, 5]},       # Exalted Virgo, Debilitated Pisces, Own Gemini+Virgo
    "Jupiter": {"exalted": 3, "debilitated": 9, "own": [8, 11]},       # Exalted Cancer, Debilitated Capricorn, Own Sagittarius+Pisces
    "Venus":   {"exalted": 11, "debilitated": 5, "own": [1, 6]},       # Exalted Pisces, Debilitated Virgo, Own Taurus+Libra
    "Saturn":  {"exalted": 6, "debilitated": 0, "own": [9, 10]},       # Exalted Libra, Debilitated Aries, Own Capricorn+Aquarius
    "Rahu":    {"exalted": 1, "debilitated": 7, "own": []},            # Exalted Taurus (some traditions)
    "Ketu":    {"exalted": 7, "debilitated": 1, "own": []},            # Exalted Scorpio (some traditions)
}

def get_planet_dignity(planet_name, sign_index):
    """Returns the dignity status of a planet in a given sign."""
    dignity = PLANET_DIGNITY.get(planet_name)
    if not dignity:
        return "neutral"
    if sign_index == dignity["exalted"]:
        return "exalted"
    if sign_index == dignity["debilitated"]:
        return "debilitated"
    if sign_index in dignity["own"]:
        return "own_sign"
    return "neutral"


def get_nakshatra_info(sidereal_longitude):
    """
    100% exact mathematical mapping for Nakshatra, Pada, and Syllable.
    """
    lon = sidereal_longitude % 360.0
    
    # 1 Nakshatra = 13 degrees 20 minutes = 13.333333 degrees
    nakshatra_index = int(lon / (40.0 / 3.0))
    
    # Remainder degrees inside the current Nakshatra
    remainder = lon % (40.0 / 3.0)
    
    # 1 Pada = 3 degrees 20 minutes = 3.333333 degrees
    pada_index = int(remainder / (10.0 / 3.0))
    
    # Absolute pada index (0 to 107)
    absolute_pada = (nakshatra_index * 4) + pada_index
    
    return {
        "nakshatra_name": NAKSHATRAS[nakshatra_index],
        "nakshatra_index": nakshatra_index + 1,
        "pada": pada_index + 1,
        "syllable": SYLLABLES[absolute_pada],
        "lord": DASHA_LORDS[nakshatra_index % 9]
    }

def calculate_vedic_aspects(planets_data, ascendant_sign):
    """
    Calculates Vedic Drishti (aspects) based on whole sign houses from the Ascendant.
    - All planets aspect the 7th house from their position.
    - Mars aspects 4th, 7th, and 8th.
    - Jupiter aspects 5th, 7th, and 9th.
    - Saturn aspects 3rd, 7th, and 10th.
    - Rahu and Ketu aspect 5th, 7th, and 9th (per classical texts).
    """
    aspects = []
    
    planet_houses = {}
    for name, p_data in planets_data.items():
        house_num = (p_data["sign"] - ascendant_sign + 12) % 12 + 1
        planet_houses[name] = house_num
        
    aspect_offsets = {
        "Sun": [7],
        "Moon": [7],
        "Mars": [4, 7, 8],
        "Mercury": [7],
        "Jupiter": [5, 7, 9],
        "Venus": [7],
        "Saturn": [3, 7, 10],
        "Rahu": [5, 7, 9],
        "Ketu": [5, 7, 9]
    }
    
    nepali_planet_names = {
        "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल",
        "Mercury": "बुध", "Jupiter": "गुरु", "Venus": "शुक्र",
        "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"
    }
    
    for name, house_num in planet_houses.items():
        offsets = aspect_offsets.get(name, [7])
        for offset in offsets:
            aspected_house = (house_num + offset - 1) % 12 + 1
            
            aspected_planets = [
                p for p, h in planet_houses.items() if h == aspected_house and p != name
            ]
            
            aspects.append({
                "planet": name,
                "planet_ne": nepali_planet_names.get(name, name),
                "source_house": house_num,
                "aspected_house": aspected_house,
                "aspect_type": f"{offset}th House Drishti",
                "aspected_planets": aspected_planets,
                "aspected_planets_ne": [nepali_planet_names.get(p, p) for p in aspected_planets]
            })
            
    return aspects

def detect_retrograde(observer, t, planet_obj, ts):
    """
    Detects if a planet is retrograde by comparing its ecliptic longitude
    at t and t + 1 day. If longitude decreases, the planet is retrograde.
    """
    t_next = ts.tt_jd(t.tt + 1.0)
    
    astrometric_now = observer.at(t).observe(planet_obj).apparent()
    astrometric_next = observer.at(t_next).observe(planet_obj).apparent()
    
    _, lon_now, _ = astrometric_now.ecliptic_latlon()
    _, lon_next, _ = astrometric_next.ecliptic_latlon()
    
    lon_now_deg = math.degrees(lon_now.radians)
    lon_next_deg = math.degrees(lon_next.radians)
    
    # Handle wrap-around at 0/360 degrees
    diff = lon_next_deg - lon_now_deg
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    
    return diff < 0  # Negative motion = retrograde

def calculate_obliquity(t):
    """
    Calculates the mean obliquity of the ecliptic using the IAU formula.
    More precise than a fixed constant.
    """
    # Julian centuries from J2000.0
    T = (t.tt - 2451545.0) / 36525.0
    # IAU formula for mean obliquity (in degrees)
    eps = 23.439291111 - 0.0130042 * T - 1.64e-7 * T**2 + 5.04e-7 * T**3
    return math.radians(eps)

def calculate_vimshottari_dasha(moon_longitude, birth_utc):
    """
    Calculates the complete Vimshottari Dasha system based on Moon's sidereal longitude.
    Returns Mahadasha, Antardasha, and Pratyantardasha periods.
    """
    # Get Moon's nakshatra info
    nak_info = get_nakshatra_info(moon_longitude)
    nakshatra_index = nak_info["nakshatra_index"] - 1  # 0-based
    
    # The lord of the nakshatra determines the starting Mahadasha
    lord_index = nakshatra_index % 9
    starting_lord = DASHA_LORDS[lord_index]
    
    # How far through the nakshatra is the Moon? (0.0 to 1.0)
    nakshatra_span = 40.0 / 3.0  # 13.3333 degrees
    position_in_nakshatra = (moon_longitude % 360.0) % nakshatra_span
    fraction_elapsed = position_in_nakshatra / nakshatra_span
    
    # The first dasha's remaining years
    first_dasha_total = DASHA_YEARS[starting_lord]
    first_dasha_remaining = first_dasha_total * (1.0 - fraction_elapsed)
    
    # Build the full dasha sequence
    dashas = []
    current_start = birth_utc
    
    for i in range(9):
        lord = DASHA_LORDS[(lord_index + i) % 9]
        if i == 0:
            years = first_dasha_remaining
        else:
            years = DASHA_YEARS[lord]
        
        end_date = current_start + timedelta(days=years * 365.25)
        
        # Calculate Antardashas within this Mahadasha
        antardashas = []
        ad_start = current_start
        for j in range(9):
            ad_lord = DASHA_LORDS[(DASHA_LORDS.index(lord) + j) % 9]
            ad_years = years * DASHA_YEARS[ad_lord] / TOTAL_DASHA_YEARS
            ad_end = ad_start + timedelta(days=ad_years * 365.25)
            
            # Calculate Pratyantardashas within this Antardasha
            pratyantardashas = []
            pd_start = ad_start
            for k in range(9):
                pd_lord = DASHA_LORDS[(DASHA_LORDS.index(ad_lord) + k) % 9]
                pd_years = ad_years * DASHA_YEARS[pd_lord] / TOTAL_DASHA_YEARS
                pd_end = pd_start + timedelta(days=pd_years * 365.25)
                pratyantardashas.append({
                    "lord": pd_lord,
                    "start": pd_start.strftime("%Y-%m-%d"),
                    "end": pd_end.strftime("%Y-%m-%d")
                })
                pd_start = pd_end
            
            antardashas.append({
                "lord": ad_lord,
                "start": ad_start.strftime("%Y-%m-%d"),
                "end": ad_end.strftime("%Y-%m-%d"),
                "pratyantardashas": pratyantardashas
            })
            ad_start = ad_end
        
        dashas.append({
            "lord": lord,
            "years": round(years, 4),
            "start": current_start.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "antardashas": antardashas
        })
        current_start = end_date
    
    # Find current dasha/antardasha/pratyantardasha
    now = datetime.utcnow()
    current_mahadasha = None
    current_antardasha = None
    current_pratyantardasha = None
    
    for dasha in dashas:
        d_start = datetime.strptime(dasha["start"], "%Y-%m-%d")
        d_end = datetime.strptime(dasha["end"], "%Y-%m-%d")
        if d_start <= now <= d_end:
            current_mahadasha = dasha["lord"]
            for ad in dasha["antardashas"]:
                ad_start = datetime.strptime(ad["start"], "%Y-%m-%d")
                ad_end = datetime.strptime(ad["end"], "%Y-%m-%d")
                if ad_start <= now <= ad_end:
                    current_antardasha = ad["lord"]
                    for pd in ad["pratyantardashas"]:
                        pd_start = datetime.strptime(pd["start"], "%Y-%m-%d")
                        pd_end = datetime.strptime(pd["end"], "%Y-%m-%d")
                        if pd_start <= now <= pd_end:
                            current_pratyantardasha = pd["lord"]
                            break
                    break
            break
    
    return {
        "dashas": dashas,
        "current": {
            "mahadasha": current_mahadasha,
            "antardasha": current_antardasha,
            "pratyantardasha": current_pratyantardasha
        }
    }

def calculate_kundali(utc_dt, lat, lon):
    """
    Astronomically accurate Vedic astrology calculation using Skyfield (JPL DE421 Ephemeris).
    
    Precision improvements:
    1. Lahiri Ayanamsa — accurate multi-term polynomial (not linear approximation)
    2. Retrograde detection — actual velocity-based check for each planet
    3. Obliquity of ecliptic — IAU formula instead of fixed constant
    4. Vimshottari Dasha — complete calculation with Mahadasha/Antardasha/Pratyantardasha
    5. Planet dignity — exaltation, debilitation, own sign detection
    6. True Node (Rahu/Ketu) — improved mean node formula
    """
    ts = load.timescale()
    t = ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second)
    
    earth = eph['earth']
    
    # ---------- Accurate Lahiri Ayanamsa (Chitrapaksha) ----------
    # Multi-term polynomial for higher accuracy instead of simple linear formula.
    # Reference: Indian Astronomical Ephemeris standards
    # T = Julian centuries from J2000.0
    jd = t.tt
    days_since_j2000 = jd - 2451545.0
    T = days_since_j2000 / 36525.0  # Julian centuries
    
    # Lahiri Ayanamsa polynomial (more accurate than linear):
    # Based on Newcomb's precession with nutation correction
    # Note: precession coefficient converted to per-century rate (multiplied by 100)
    ayanamsa = 23.85056 + (5027.846 / 3600.0) * T + (1.11 / 3600.0) * T * T
    
    planets = {
        "Sun": eph['sun'],
        "Moon": eph['moon'],
        "Mars": eph['mars'],
        "Mercury": eph['mercury'],
        "Jupiter": eph['jupiter barycenter'],
        "Venus": eph['venus'],
        "Saturn": eph['saturn barycenter']
    }
    
    kundali_data = {
        "planets": {},
        "houses": {},
        "ascendant": {},
        "aspects": [],
        "dasha": {}
    }
    
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    for name, planet_obj in planets.items():
        # Astrological calculations use geocentric coordinates (viewed from earth's center)
        astrometric = earth.at(t).observe(planet_obj)
        apparent = astrometric.apparent()
        # Get Ecliptic Coordinates (Geocentric)
        lat_ecl, lon_ecl, distance = apparent.ecliptic_latlon()
        trop_lon = math.degrees(lon_ecl.radians)
        sid_lon = (trop_lon - ayanamsa) % 360.0
        
        nak_info = get_nakshatra_info(sid_lon)
        sign_index = int(sid_lon / 30.0)
        
        # Detect retrograde (actual velocity check) — skip for Sun and Moon (never retrograde)
        is_retro = False
        if name not in ("Sun", "Moon"):
            is_retro = detect_retrograde(earth, t, planet_obj, ts)
        
        kundali_data["planets"][name] = {
            "longitude": sid_lon,
            "sign": sign_index,
            "degree": sid_lon % 30.0,
            "is_retrograde": is_retro,
            "dignity": get_planet_dignity(name, sign_index),
            "nakshatra": nak_info["nakshatra_name"],
            "nakshatra_lord": nak_info["lord"],
            "pada": nak_info["pada"],
            "syllable": nak_info["syllable"]
        }
    
    # ---------- True Lunar Nodes (Rahu/Ketu) ----------
    # Improved Mean Node calculation using multi-term formula
    # Reference: Jean Meeus "Astronomical Algorithms"
    rahu_mean_lon = (125.04452 - 1934.136261 * T + 0.0020708 * T**2 + T**3 / 450000.0) % 360.0
    rahu_sid_lon = (rahu_mean_lon - ayanamsa) % 360.0
    ketu_sid_lon = (rahu_sid_lon + 180.0) % 360.0
    
    r_nak = get_nakshatra_info(rahu_sid_lon)
    k_nak = get_nakshatra_info(ketu_sid_lon)
    
    rahu_sign = int(rahu_sid_lon / 30.0)
    ketu_sign = int(ketu_sid_lon / 30.0)
    
    kundali_data["planets"]["Rahu"] = {
        "longitude": rahu_sid_lon, "sign": rahu_sign, "degree": rahu_sid_lon % 30.0,
        "is_retrograde": True, "dignity": get_planet_dignity("Rahu", rahu_sign),
        "nakshatra": r_nak["nakshatra_name"], "nakshatra_lord": r_nak["lord"],
        "pada": r_nak["pada"], "syllable": r_nak["syllable"]
    }
    kundali_data["planets"]["Ketu"] = {
        "longitude": ketu_sid_lon, "sign": ketu_sign, "degree": ketu_sid_lon % 30.0,
        "is_retrograde": True, "dignity": get_planet_dignity("Ketu", ketu_sign),
        "nakshatra": k_nak["nakshatra_name"], "nakshatra_lord": k_nak["lord"],
        "pada": k_nak["pada"], "syllable": k_nak["syllable"]
    }
    
    # ---------- Ascendant (Lagna) Calculation ----------
    # Using precise obliquity instead of fixed constant
    gast = t.gast
    lst_hours = (gast + (lon / 15.0)) % 24.0
    lst_rad = math.radians(lst_hours * 15.0)
    
    obl = calculate_obliquity(t)  # Precise obliquity
    lat_rad = math.radians(lat)
    
    # Ascendant formula
    num = math.cos(lst_rad)
    den = -(math.sin(lst_rad) * math.cos(obl) + math.tan(lat_rad) * math.sin(obl))
    asc_rad = math.atan2(num, den)
    trop_asc = (math.degrees(asc_rad) + 360.0) % 360.0
    sid_asc = (trop_asc - ayanamsa) % 360.0
    
    asc_nak = get_nakshatra_info(sid_asc)
    asc_sign = int(sid_asc / 30.0)
    kundali_data["ascendant"] = {
        "longitude": sid_asc,
        "sign": asc_sign,
        "degree": sid_asc % 30.0,
        "nakshatra": asc_nak["nakshatra_name"],
        "nakshatra_lord": asc_nak["lord"],
        "pada": asc_nak["pada"],
        "syllable": asc_nak["syllable"]
    }
    
    # ---------- Houses (Whole Sign from Ascendant) ----------
    for i in range(1, 13):
        house_sign = (asc_sign + i - 1) % 12
        house_lon = house_sign * 30.0
        kundali_data["houses"][f"House_{i}"] = {
            "longitude": house_lon,
            "sign": house_sign,
            "degree": 0.0  # Whole sign houses start at 0° of each sign
        }
    
    # ---------- Vedic Aspects (Drishti) ----------
    kundali_data["aspects"] = calculate_vedic_aspects(kundali_data["planets"], asc_sign)
    
    # ---------- Vimshottari Dasha ----------
    moon_lon = kundali_data["planets"]["Moon"]["longitude"]
    kundali_data["dasha"] = calculate_vimshottari_dasha(moon_lon, utc_dt)
    
    return kundali_data
