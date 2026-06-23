import ephem
import math

def test_ephem():
    obs = ephem.Observer()
    obs.lon = str(-0.1278) # London
    obs.lat = str(51.5074)
    obs.date = '1990/05/15 14:30:00' # UTC
    
    sun = ephem.Sun(obs)
    ecl = ephem.Ecliptic(sun)
    lon_deg = math.degrees(ecl.lon)
    
    print(f"Sun Tropical Longitude: {lon_deg}")
    
    # Approx Lahiri
    year = 1990 + (5/12.0)
    ayanamsa = 23.853 + (year - 2000) * 0.013969
    print(f"Ayanamsa: {ayanamsa}")
    
    sidereal_lon = (lon_deg - ayanamsa) % 360
    print(f"Sun Sidereal Longitude: {sidereal_lon}")

if __name__ == "__main__":
    test_ephem()
