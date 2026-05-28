# DEFRA 2023 emission factors — kg CO2e per litre of fuel
# Source: UK Government GHG Conversion Factors for Company Reporting 2023
DEFRA_2023 = {
    "DIESEL":       2.51839,
    "PETROL":       2.31489,
    "UNLEADED":     2.31489,  # alias for petrol
    "HSD":          2.51839,  # High Speed Diesel (common SAP material code)
    "LDO":          2.75760,  # Light Diesel Oil
    "FURNACE_OIL":  3.17880,  # Heavy fuel oil
}

EMISSION_FACTOR_SOURCE = "DEFRA_2023"

# EPA eGRID 2023 emission factors — kg CO2e per kWh of electricity
# Source: US EPA eGRID 2023 (https://www.epa.gov/egrid)
# Key: grid region subregion code. Use "US_AVG" when region is unknown.
EGRID_2023 = {
    "US_AVG":   0.3861,   # US national average
    "WECC":     0.2710,   # Western US
    "RFC":      0.3617,   # Mid-Atlantic / Great Lakes
    "SERC":     0.4012,   # Southeast US
    "TRE":      0.3988,   # Texas (ERCOT)
    "NPCC":     0.2185,   # Northeast US / New England
    # India CEA 2023 — included because SAP plants are India-based
    "IN_CEA":   0.7160,   # India Central Electricity Authority 2023
}

EGRID_EMISSION_FACTOR_SOURCE = "EPA_EGRID_2023"
DEFAULT_GRID_REGION = "US_AVG"

# Utility unit → kWh conversion factors
TO_KWH = {
    "KWH":  1.0,
    "MWH":  1000.0,
    "GWH":  1_000_000.0,
}

# ── Travel emission factors (DEFRA 2023) ─────────────────────────────────────

# Flights: kg CO2e per passenger per km (includes radiative forcing at 1.891×)
# ClassOfService codes: Y/M/S/H/Q/K = Economy, W/B = Premium Economy,
#                       C/D/J/Z = Business, F/A/P = First
# Source: DEFRA 2023 GHG Conversion Factors — Passenger flights
FLIGHT_EMISSION_FACTOR_KG_PER_PKM = 0.19085   # economy long-haul base
FLIGHT_CABIN_MULTIPLIERS = {
    "ECONOMY":          1.0,
    "PREMIUM_ECONOMY":  1.6,
    "BUSINESS":         2.9,
    "FIRST":            4.0,
}
# Map Concur ClassOfService single-letter codes → cabin category
CONCUR_CLASS_MAP = {
    "Y": "ECONOMY", "M": "ECONOMY", "S": "ECONOMY", "H": "ECONOMY",
    "Q": "ECONOMY", "K": "ECONOMY", "L": "ECONOMY", "U": "ECONOMY",
    "W": "PREMIUM_ECONOMY", "B": "PREMIUM_ECONOMY",
    "C": "BUSINESS", "D": "BUSINESS", "J": "BUSINESS", "Z": "BUSINESS",
    "F": "FIRST", "A": "FIRST", "P": "FIRST",
}
DEFAULT_CABIN_CLASS = "ECONOMY"   # fallback when ClassOfService is missing

TRAVEL_EMISSION_FACTOR_SOURCE = "DEFRA_2023"

# Hotels: kg CO2e per room per night (DEFRA 2023 UK average)
HOTEL_EMISSION_FACTOR_KG_PER_NIGHT = 20.8

# Cars: kg CO2e per rental day (assumes ~100 km/day × 0.17 kg CO2e/km average car)
CAR_EMISSION_FACTOR_KG_PER_DAY = 17.0

# Airport coordinates for great-circle distance — (lat, lon) in decimal degrees
# Source: OpenFlights.org airport database
AIRPORT_COORDS = {
    "DEL": (28.5665, 77.1031),   # Indira Gandhi International, Delhi
    "BOM": (19.0896, 72.8656),   # Chhatrapati Shivaji, Mumbai
    "LHR": (51.4775, -0.4614),   # Heathrow, London
    "LGW": (51.1537, -0.1821),   # Gatwick, London
    "JFK": (40.6413, -73.7781),  # John F. Kennedy, New York
    "EWR": (40.6895, -74.1745),  # Newark, New York
    "CDG": (49.0097,  2.5478),   # Charles de Gaulle, Paris
    "DXB": (25.2532, 55.3657),   # Dubai International
    "SIN": ( 1.3644, 103.9915),  # Changi, Singapore
    "HKG": (22.3080, 113.9185),  # Hong Kong International
    "SYD": (-33.9461, 151.1772), # Kingsford Smith, Sydney
    "LAX": (33.9425, -118.4081), # Los Angeles International
    "ORD": (41.9742, -87.9073),  # O'Hare, Chicago
    "ATL": (33.6407, -84.4277),  # Hartsfield-Jackson, Atlanta
    "BLR": (13.1979,  77.7063),  # Kempegowda, Bengaluru
    "HYD": (17.2403,  78.4294),  # Rajiv Gandhi, Hyderabad
    "MAA": (12.9941,  80.1709),  # Chennai International
    "CCU": (22.6547,  88.4467),  # Netaji Subhas, Kolkata
    "AMD": (23.0772,  72.6347),  # Sardar Vallabhbhai Patel, Ahmedabad
}

# Unit → litres conversion factors
# SAP OrderQuantityUnit values vary; map common ones to litres
TO_LITRES = {
    "L":    1.0,
    "LT":   1.0,       # SAP alternate code for litre
    "LTR":  1.0,
    "GAL":  3.78541,   # US gallon
    "GL":   3.78541,
    "UKGAL": 4.54609,  # UK/Imperial gallon
    "M3":   1000.0,    # cubic metre
    "KL":   1000.0,    # kilolitre
}

# Fuel density kg/L (used when unit is KG — convert mass → volume → CO2e)
FUEL_DENSITY_KG_PER_L = {
    "DIESEL":   0.832,
    "HSD":      0.832,
    "PETROL":   0.755,
    "UNLEADED": 0.755,
    "LDO":      0.820,
    "FURNACE_OIL": 0.950,
}
