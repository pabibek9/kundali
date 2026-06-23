/**
 * Vedic Astrological Calculator utilizing the 'swisseph' NPM package.
 * Ensure you install via: npm install swisseph
 */

import * as swisseph from 'swisseph';

// Nakshatras 27 array
const NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", 
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
];

// 108 Syllables exactly mapped
const SYLLABLES = [
    "Chu", "Che", "Cho", "La", "Li", "Lu", "Le", "Lo", "A", "I", "U", "E",
    "O", "Va", "Vi", "Vu", "Ve", "Vo", "Ka", "Ki", "Ku", "Gha", "Ng", "Chha",
    "Ke", "Ko", "Ha", "Hi", "Hu", "He", "Ho", "Da", "Di", "Du", "De", "Do",
    "Ma", "Mi", "Mu", "Me", "Mo", "Ta", "Ti", "Tu", "Te", "To", "Pa", "Pi",
    "Pu", "Sha", "Na", "Tha", "Pe", "Po", "Ra", "Ri", "Ru", "Re", "Ro", "Ta",
    "Ti", "Tu", "Te", "To", "Na", "Ni", "Nu", "Ne", "No", "Ya", "Yi", "Yaa", // Jyeshtha Pada 4 is Yaa
    "Ye", "Yo", "Ba", "Bi", "Bu", "Dha", "Bha", "Dha", "Be", "Bo", "Ja", "Ji",
    "Ju", "Je", "Jo", "Gha", "Ga", "Gi", "Gu", "Ge", "Go", "Sa", "Si", "Su",
    "Se", "So", "Da", "Di", "Du", "Tha", "Jha", "Na", "De", "Do", "Cha", "Chi"
];

export interface PlanetaryPosition {
    longitude: number;
    sign: number;
    degreeInSign: number;
    nakshatra: string;
    pada: number;
    syllable: string;
    isRetrograde: boolean;
}

/**
 * 100% exact mathematical mapping for Nakshatras and Padas.
 */
function getNakshatraDetails(longitude: number) {
    const lon = longitude % 360.0;
    
    // 1 Nakshatra = 13° 20' = 13.333333°
    const nakshatraIndex = Math.floor(lon / (40.0 / 3.0));
    
    // Remainder inside the nakshatra
    const remainder = lon % (40.0 / 3.0);
    
    // 1 Pada = 3° 20' = 3.333333°
    const padaIndex = Math.floor(remainder / (10.0 / 3.0));
    
    const absolutePada = (nakshatraIndex * 4) + padaIndex;

    return {
        nakshatraName: NAKSHATRAS[nakshatraIndex],
        pada: padaIndex + 1,
        syllable: SYLLABLES[absolutePada]
    };
}

/**
 * Main Calculator
 * Converts UTC timestamp and Coordinates to exact Sidereal Astrological JSON
 */
export function calculateVedicKundali(
    year: number, month: number, day: number, 
    hour: number, minute: number, second: number, 
    lat: number, lon: number
): any {
    
    // Configure Swiss Ephemeris paths if using actual ephe files
    // swisseph.swe_set_ephe_path('/path/to/ephe');

    // Flag for exact Sidereal mode using Lahiri Ayanamsa
    swisseph.swe_set_sid_mode(swisseph.SE_SIDM_LAHIRI, 0, 0);
    const flags = swisseph.SEFLG_SWIEPH | swisseph.SEFLG_SIDEREAL | swisseph.SEFLG_SPEED;

    // Get Julian Day in Universal Time
    const jd_ut = swisseph.swe_julday(year, month, day, hour + (minute/60) + (second/3600), swisseph.SE_GREG_CAL);

    const planetMap = [
        { name: "Sun", id: swisseph.SE_SUN },
        { name: "Moon", id: swisseph.SE_MOON },
        { name: "Mars", id: swisseph.SE_MARS },
        { name: "Mercury", id: swisseph.SE_MERCURY },
        { name: "Jupiter", id: swisseph.SE_JUPITER },
        { name: "Venus", id: swisseph.SE_VENUS },
        { name: "Saturn", id: swisseph.SE_SATURN },
        { name: "Rahu", id: swisseph.SE_TRUE_NODE }
    ];

    let result: any = { planets: {} };

    // Planet Loop
    planetMap.forEach(p => {
        const calc = swisseph.swe_calc_ut(jd_ut, p.id, flags);
        const longitude = calc.longitude;
        const speed = calc.longitudeSpeed;
        const nakInfo = getNakshatraDetails(longitude);

        result.planets[p.name] = {
            longitude: longitude,
            sign: Math.floor(longitude / 30),
            degreeInSign: longitude % 30,
            isRetrograde: speed < 0,
            nakshatra: nakInfo.nakshatraName,
            pada: nakInfo.pada,
            syllable: nakInfo.syllable
        };
    });

    // Ketu is 180 degrees from Rahu
    const rahuLon = result.planets["Rahu"].longitude;
    const ketuLon = (rahuLon + 180.0) % 360.0;
    const ketuNak = getNakshatraDetails(ketuLon);
    result.planets["Ketu"] = {
        longitude: ketuLon,
        sign: Math.floor(ketuLon / 30),
        degreeInSign: ketuLon % 30,
        isRetrograde: true,
        nakshatra: ketuNak.nakshatraName,
        pada: ketuNak.pada,
        syllable: ketuNak.syllable
    };

    // Calculate Houses and Exact Ascendant (Placidus system 'P')
    const houses = swisseph.swe_houses_ex(jd_ut, flags, lat, lon, 'P');
    
    const ascLongitude = houses.ascendant;
    const ascNak = getNakshatraDetails(ascLongitude);

    result.ascendant = {
        longitude: ascLongitude,
        sign: Math.floor(ascLongitude / 30),
        degreeInSign: ascLongitude % 30,
        nakshatra: ascNak.nakshatraName,
        pada: ascNak.pada,
        syllable: ascNak.syllable
    };

    return result;
}
