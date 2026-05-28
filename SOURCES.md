# SOURCES.md — Research Behind Each Data Source

## Source 1 — SAP OData V4 (Scope 1 Fuel Combustion)

**What real-world format was researched:**
SAP API Business Hub — `API_PURCHASEORDER_PROCESS_SRV` (Purchase Order Process API, OData V4).
URL: `https://api.sap.com/api/API_PURCHASEORDER_PROCESS_SRV/overview`

**Specific docs read:**
- SAP API Business Hub entity model for `A_PurchaseOrderItem` — field list including `Material`, `OrderQuantity`, `OrderQuantityUnit`, `DocumentDate`, `Plant`, `Supplier`.
- DEFRA 2025 GHG Conversion Factors for Company Reporting (UK Government, published March 2025) — Table 1 (Fuels), columns "kg CO2e per litre" for diesel, petrol, LDO, and heavy fuel oil.
- SAP material master naming conventions: HSD (High Speed Diesel), LDO (Light Diesel Oil), FURNACE_OIL are common Indian plant material codes for fuel.

**Why the sample data looks the way it does:**
- 10 valid rows covering 6 fuel types (DIESEL, PETROL, HSD, LDO, FURNACE_OIL, UNLEADED) with mixed units (L, GAL, LTR, KL, KG) to exercise all unit conversion branches.
- 2 rows with a missing `OrderQuantityUnit` field to test the hard-fail error path.
- Plant codes `PLANT_MH01` (Mumbai) and `PLANT_DL02` (Delhi) reflect that the organisation operates Indian manufacturing facilities.

**What would break in a real deployment:**
- A live SAP system may contain material codes not in the current constants.py lookup (e.g., CNG, aviation fuel, lubricating oil). The parser raises `SAPParseError` for unknown materials — those rows would appear as failed in the ingestion run.
- SAP `DocumentDate` sometimes contains the format `YYYYMMDD` (no hyphens) from older BAPI exports. The parser handles three date formats but not all regional variations.
- Large exports (year-end PO dump) could contain 50,000+ rows and exceed the synchronous request timeout. See TRADEOFFS.md.

---

## Source 2 — Utility / Green Button CSV (Scope 2 Purchased Electricity)

**What real-world format was researched:**
Green Button Alliance — "Green Button Download My Data" CSV export specification.
URL: `https://www.greenbuttonalliance.org/`

NAESB REQ.21 standard column definitions:
`ACCOUNT_NUMBER`, `METER_ID`, `INTERVAL_START`, `INTERVAL_END`, `USAGE`, `UNIT`, `COST`

**Specific docs read:**
- Green Button Alliance sample data repository (GitHub: `green-button/green-button-data`) — CSV export format.
- EPA eGRID 2023 Summary Tables (published January 2024) — subregion average emission rates (lb CO2e/MWh, converted to kg CO2e/kWh).
- US DOE Energy Information Administration: explanation of why utility billing periods are 28–33 days (meter reading cycles tied to field crew routes, not calendar months).

**Why the sample data looks the way it does:**
- Two meter IDs (`METER_BLD_A`, `METER_BLD_B`) represent two buildings — demonstrating that one organisation has multiple meters.
- Billing periods are intentionally non-calendar (e.g., March 5 – April 3) to match real utility meter reading cycles.
- One row uses MWh instead of kWh to test the `TO_KWH` unit conversion.
- Usage values are in the 1,500–2,500 kWh range, typical for a small commercial building per billing cycle.

**What would break in a real deployment:**
- Some utility providers export in XML (ESPI format) rather than CSV. The current parser only handles CSV.
- The grid region is not in the CSV — the parser defaults to `US_AVG`. A real deployment would require a mapping from meter ID to eGRID subregion (e.g., from the utility account metadata).
- Daylight saving time transitions can cause `INTERVAL_START`/`INTERVAL_END` to be ambiguous. The parser stores them as-is without timezone normalisation.

---

## Source 3 — Concur Travel Itinerary (Scope 3 Category 6 Business Travel)

**What real-world format was researched:**
SAP Concur Developer Center — Itinerary v1 API (TMC/Third-party).
URL: `https://developer.concur.com/api-reference/travel/itinerary-tmc-thirdparty/`

**Specific docs read:**
- Concur Itinerary v1 field reference: `Itinerary`, `Segments`, `Air`, `Hotel`, `Car` objects.
- Key fields extracted: `StartCityCode`, `EndCityCode`, `ClassOfService` (Air); `StartDateLocal`, `EndDateLocal` (Hotel); `PickupDeliveryCity`, `StartDateLocal`, `EndDateLocal` (Car).
- DEFRA 2025 GHG Conversion Factors — Section 6 (Business Travel), Table 6a (Passenger flights by cabin class, kg CO2e per passenger-km including radiative forcing factor of 1.891×).
- OpenFlights.org airport database (openly licensed, CC BY) — latitude/longitude per IATA code, used as input to the haversine great-circle distance formula.
- DEFRA 2025 — Hotel accommodation emission factor (kg CO2e per room per night).

**Why the sample data looks the way it does:**
- Trip `TRP001`: DEL→BOM Economy + Hotel 2 nights + Car 2 days — a realistic domestic Indian business trip.
- Trip `TRP002`: BOM→LHR Business class + Hotel 3 nights — an international trip in a premium cabin to test the 2.9× multiplier.
- Trip `TRP003`: LHR→JFK with no `ClassOfService` field — tests the ECONOMY fallback default.
- Real IATA codes are used so the haversine calculation produces meaningful distances (DEL→BOM ≈ 1,148 km, BOM→LHR ≈ 7,192 km).

**What would break in a real deployment:**
- The IATA coordinate dictionary in `constants.py` contains 20 airports. Any flight using an airport not in the list raises a `KeyError`. A production deployment would need to load the full OpenFlights database (~7,000 airports).
- Concur's live API uses a Company-level OAuth token — the current implementation accepts a JSON payload directly without authentication against Concur's servers.
- Multi-leg itineraries (e.g., DEL→DXB→LHR with a stopover) are not handled — the parser treats each Air segment as an independent direct flight. Actual routing distance would be the sum of individual legs, which the current code does not aggregate.
