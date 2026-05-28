# DECISIONS.md — Engineering Decisions & Reasoning

## 1. Why OData V4 for SAP (not IDoc or flat-file export)

SAP exposes procurement data through multiple integration channels — IDoc, BAPI, flat-file exports, and OData REST APIs. I chose OData V4 (`API_PURCHASEORDER_PROCESS_SRV`) because:

- It returns structured JSON that maps cleanly to a Python dict without custom EDI parsing.
- OData V4 is SAP's recommended integration standard for new projects (vs. IDoc which is legacy EDI format requiring a middleware adapter).
- The `value` array in an OData response lets you process rows iteratively without loading a large XML document into memory.
- Field names like `Material`, `OrderQuantity`, `OrderQuantityUnit`, and `DocumentDate` are self-documenting and map directly to emission factor lookup keys.

**Subset of SAP reality handled:** Real SAP purchase orders contain hundreds of fields (tax codes, document types, account assignments). I scoped down to 7 fields relevant to fuel quantity and date. This is intentional — ingesting the whole PO document would add noise without improving emissions accuracy.

---

## 2. Why Green Button CSV for utility (not PDF bills or API)

Utility providers in the US and increasingly in India expose consumption data via the Green Button standard. I chose it because:

- It is a recognised open standard (NAESB REQ.21) adopted by US DOE, meaning the column names (`ACCOUNT_NUMBER`, `METER_ID`, `INTERVAL_START`, `INTERVAL_END`, `USAGE`, `UNIT`) are consistent across providers.
- CSV is the most common export format — the "Green Button Download My Data" option on most utility portals produces exactly this structure.
- PDF bills are not machine-readable without OCR, which adds error-prone complexity.
- A REST API pull would require OAuth setup with each utility provider, which varies by provider.

**Non-calendar billing periods:** Utility billing periods are typically 28–33 days, not calendar months. The parser stores `INTERVAL_START` and `INTERVAL_END` verbatim and uses them as `period_start`/`period_end` on the NormalizedRecord. This preserves the actual metering window rather than forcing a calendar approximation.

---

## 3. Why Concur Itinerary API (not expense report CSV)

Corporate travel emissions require flight distance, cabin class, and segment-level detail. I chose the Concur Itinerary v1 format because:

- Expense reports aggregate costs but lose the route information needed for distance-based emission calculation.
- The Itinerary format gives `StartCityCode`, `EndCityCode`, `ClassOfService`, and date per segment — exactly what is needed to apply DEFRA cabin-class multipliers.
- Air, Hotel, and Car segments are all present in one itinerary object, avoiding multiple API calls per trip.

---

## 4. How missing units in SAP data are handled

Two rows in the sample data have no `OrderQuantityUnit`. The parser raises `SAPParseError("Missing OrderQuantityUnit for material...")` for those rows. The ingestion run records them as failed rows with the error message. This is a deliberate hard-fail rather than a guess: applying the wrong unit conversion (e.g., treating KG as litres) would produce silently wrong CO2e values that pass review undetected. It is better to surface the data quality issue explicitly.

---

## 5. How distance is calculated from airport codes

The travel parser uses the haversine great-circle distance formula with airport coordinates from the OpenFlights.org database (lat/lon per IATA code). The formula gives straight-line distance in km, which is the industry-standard input for flight emission factor tables (DEFRA 2025 uses km-based per-passenger-km factors). A full routing distance (accounting for actual flight paths) is not used because it requires a live flight data API and varies by airline; great-circle distance is the DEFRA-recommended approximation.

---

## 6. How missing ClassOfService is handled in travel data

When `ClassOfService` is absent or not in the known mapping, the parser defaults to `ECONOMY`. This is the most conservative assumption — Business class has a 2.9× multiplier and First has 4.0×. Defaulting to Economy (1.0×) means we may undercount emissions for upgraded travel, but we do not fabricate a cabin class. The fallback is documented in constants.py and in the ReviewAction audit trail.

---

## 7. Scope 1/2/3 assignment

| Source | Scope | Reason |
|--------|-------|--------|
| SAP fuel purchase | 1 | Direct combustion of fuel owned/controlled by the company |
| Utility electricity | 2 | Purchased electricity — emissions happen at the power plant |
| Concur travel | 3 Category 6 | Business travel in vehicles not owned by the company |

This follows GHG Protocol Corporate Standard definitions exactly.

---

## 8. What I would ask the PM before going to production

1. **Grid region per meter:** The eGRID emission factor varies by 2× between NPCC (Northeast US) and SERC (Southeast US). Which grid region does each building meter belong to? Without this, I default to the US national average, which may over- or under-count significantly.

2. **SAP material code vocabulary:** The current parser handles DIESEL, PETROL, HSD, LDO, FURNACE_OIL, UNLEADED. Are there other material codes in the live SAP system (e.g., CNG, LPG, aviation fuel) that should be included?

3. **Review ownership:** Who has authority to approve a flagged record — the analyst who flagged it, their manager, or any analyst? The current model allows any authenticated user to approve any record. A role-based permission model would need a product decision on the approval hierarchy.
