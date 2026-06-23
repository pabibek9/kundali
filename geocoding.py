from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def search_place(place_name):
    """
    Searches for a place using Nominatim and returns a list of potential matches.
    """
    geolocator = Nominatim(user_agent="janam_kundali_app")
    try:
        # Get multiple results to handle ambiguity
        locations = geolocator.geocode(place_name, exactly_one=False, limit=5)
        
        if not locations:
            return []
            
        return locations
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Error connecting to geocoding service: {e}")
        return None

def format_location_options(locations):
    """
    Formats the list of geopy locations for user display.
    """
    options = []
    for i, loc in enumerate(locations):
        options.append({
            "index": i + 1,
            "address": loc.address,
            "latitude": loc.latitude,
            "longitude": loc.longitude
        })
    return options
