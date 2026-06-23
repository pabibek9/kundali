import ephem
import math

def test_ephem():
    obs = ephem.Observer()
    obs.lon = str(-0.1278) # London
    obs.lat = str(51.5074)
    obs.date = '1990/05/15 14:30:00' # UTC
    
    lst = float(obs.sidereal_time()) # radians
    lat = float(obs.lat)
    obl = math.radians(23.4392911)
    
    num = math.cos(lst)
    den = -math.sin(lst) * math.cos(obl) - math.tan(lat) * math.sin(obl)
    asc_rad = math.atan2(num, den)
    asc_deg = (math.degrees(asc_rad) + 360) % 360
    
    print("Tropical Asc:", asc_deg)
    
    # Rahu (Mean North Node)
    # JD for J2000 is 2451545.0
    # ephem.Date('2000/01/01 12:00:00') is the epoch
    d_epoch = ephem.Date('2000/01/01 12:00:00')
    days_since_j2000 = obs.date - d_epoch
    
    rahu_mean_lon = (125.0445 - 0.0529537648 * days_since_j2000) % 360
    print("Rahu Mean Trop Lon:", rahu_mean_lon)

if __name__ == "__main__":
    test_ephem()
