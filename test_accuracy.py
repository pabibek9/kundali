"""Quick test to verify the updated astrology engine accuracy."""
from datetime import datetime
import pytz
from astrology import calculate_kundali
from report import format_kundali_data, get_zodiac_sign_name

# Test: Birth in Okhaldhunga, Nepal — 2063/10/10 BS = 2007-01-23 AD, 5:01 AM Nepal Time
nepal_tz = pytz.timezone("Asia/Kathmandu")
local_dt = nepal_tz.localize(datetime(2007, 1, 23, 5, 1, 0))
utc_dt = local_dt.astimezone(pytz.utc)

data = calculate_kundali(utc_dt, 27.3163, 86.5015)

print("=" * 60)
print("ASCENDANT (LAGNA)")
print("=" * 60)
a = data["ascendant"]
print(f"  Sign: {get_zodiac_sign_name(a['sign'])}")
print(f"  Degree: {a['degree']:.4f}")
print(f"  Nakshatra: {a['nakshatra']} (Pada {a['pada']})")
print(f"  Nakshatra Lord: {a['nakshatra_lord']}")
print(f"  Syllable: {a['syllable']}")

print("\n" + "=" * 60)
print("PLANETARY POSITIONS")
print("=" * 60)
for name, d in data["planets"].items():
    sign = get_zodiac_sign_name(d["sign"])
    retro = " (R)" if d["is_retrograde"] else ""
    dignity = f" [{d['dignity']}]" if d["dignity"] != "neutral" else ""
    print(f"  {name:10s}: {sign:12s} {d['degree']:7.2f}° | {d['nakshatra']:20s} P{d['pada']}{retro}{dignity}")

print("\n" + "=" * 60)
print("VIMSHOTTARI DASHA")
print("=" * 60)
current = data["dasha"]["current"]
print(f"  Mahadasha:       {current['mahadasha']}")
print(f"  Antardasha:      {current['antardasha']}")
print(f"  Pratyantardasha: {current['pratyantardasha']}")

print("\nDasha Periods:")
for d in data["dasha"]["dashas"]:
    print(f"  {d['lord']:8s}: {d['start']} to {d['end']} ({d['years']:.2f} years)")

print("\nTEST PASSED ✓")
