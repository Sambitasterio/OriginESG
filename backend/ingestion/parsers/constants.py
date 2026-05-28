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
