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
