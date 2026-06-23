# Janam Kundali Generator

A simple Python Command Line Application that generates a Janam Kundali (birth chart) from a person's name, date of birth, time of birth, and place of birth. 

It handles everything automatically:
1. **Geocoding:** Converts place names into coordinates, and gracefully handles ambiguous or invalid locations by offering choices.
2. **Timezone:** Automatically detects the time zone based on the location coordinates.
3. **Astrology:** Uses the `pyswisseph` library to calculate planetary positions, Ascendant, House Cusps (Placidus), and basic planetary aspects based on the Sidereal Zodiac (Lahiri Ayanamsa).
4. **JSON Export:** Dumps the finalized Kundali data into a cleanly formatted JSON file.

## Requirements & Installation

This app relies on the `pyswisseph` library, which requires compiling a C extension.
**IMPORTANT for Windows Users:** You MUST have the [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) installed to successfully run `pip install pyswisseph`, especially if you are using a newer version of Python (e.g. 3.13 or 3.14) where pre-compiled wheels aren't yet available.

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the `main.py` script and follow the interactive prompts:
```bash
python main.py
```

### Sample Input
```text
=== Janam Kundali Generator ===
Enter Full Name: Sample Person
Enter Date of Birth (YYYY-MM-DD): 1990-05-15
Enter Time of Birth (HH:MM, 24-hour format): 14:30
Enter Place of Birth (City, Country): London
```

The system will search for "London" and ask you to select the correct location if multiple matches are found. Afterwards, it calculates the data and saves it to a file named `sample_person_kundali.json`. You can see a reference output in `sample_output.json`.

## Architecture
- `main.py`: Entry point handling inputs and flow.
- `geocoding.py`: Handles coordinates lookup using `geopy` and Nominatim.
- `time_utils.py`: Extracts timezone data with `timezonefinder` and computes the UTC Julian Day for accurate calculations.
- `astrology.py`: The core computation engine utilizing `pyswisseph` for the Kundali properties.
- `report.py`: Translates raw numeric data into human-readable strings and formats the final JSON payload.
