import sys
from geocoding import search_place, format_location_options
from time_utils import get_timezone_from_coords, get_utc_time
from astrology import calculate_kundali
from report import format_kundali_data, save_report_to_json

def get_user_input():
    print("=== Janam Kundali Generator ===")
    name = input("Enter Full Name: ")
    date_str = input("Enter Date of Birth (YYYY-MM-DD): ")
    time_str = input("Enter Time of Birth (HH:MM, 24-hour format): ")
    place_name = input("Enter Place of Birth (City, Country): ")
    return name, date_str, time_str, place_name

def main():
    name, date_str, time_str, place_name = get_user_input()
    
    print(f"\nSearching for location: {place_name}...")
    locations = search_place(place_name)
    
    if locations is None:
        print("Failed to connect to the geocoding service. Please try again later.")
        sys.exit(1)
        
    if not locations:
        print(f"Could not find any location matching '{place_name}'.")
        sys.exit(1)
        
    selected_loc = None
    if len(locations) == 1:
        selected_loc = locations[0]
        print(f"Found location: {selected_loc.address}")
    else:
        print("\nMultiple locations found. Please select the correct one:")
        options = format_location_options(locations)
        for opt in options:
            print(f"{opt['index']}. {opt['address']}")
            
        while True:
            try:
                choice = int(input("\nEnter the number of your choice: "))
                if 1 <= choice <= len(options):
                    selected_loc = locations[choice - 1]
                    break
                else:
                    print("Invalid choice. Please enter a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
    lat = selected_loc.latitude
    lon = selected_loc.longitude
    print(f"\nCoordinates: Latitude {lat:.4f}, Longitude {lon:.4f}")
    
    print("Detecting Timezone...")
    tz_name = get_timezone_from_coords(lat, lon)
    if not tz_name:
        print("Could not determine timezone for the selected location.")
        sys.exit(1)
    print(f"Timezone detected: {tz_name}")
    
    try:
        utc_dt = get_utc_time(date_str, time_str, tz_name)
    except Exception as e:
        print(f"Error parsing date/time: {e}")
        print("Please make sure you entered the date in YYYY-MM-DD and time in HH:MM format.")
        sys.exit(1)
        
    print(f"UTC Time: {utc_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\nCalculating Kundali...")
    kundali_data = calculate_kundali(utc_dt, lat, lon)
    
    user_info = {
        "name": name,
        "date_of_birth": date_str,
        "time_of_birth": time_str,
        "place_of_birth": selected_loc.address,
        "latitude": lat,
        "longitude": lon,
        "timezone": tz_name
    }
    
    report = format_kundali_data(user_info, kundali_data)
    
    filename = f"{name.replace(' ', '_').lower()}_kundali.json"
    save_report_to_json(report, filename)
    print(f"\nSuccess! Janam Kundali report saved to {filename}")

if __name__ == "__main__":
    main()
