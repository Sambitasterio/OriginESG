# TRADEOFFS.md — Deliberate Scope Decisions

## 1. No real OAuth flow for SAP or Concur — mocked API calls

**What was skipped:** In production, pulling data from SAP OData requires an OAuth 2.0 client-credentials token exchange with SAP BTP (Business Technology Platform). Concur similarly requires a Company-level JWT token obtained through the App Center OAuth flow.

**Why it was skipped:** Setting up a real SAP sandbox or Concur developer account requires corporate credentials, a registered application in SAP BTP, and typically a 2–5 day approval process. This is an integration concern, not an emissions logic concern. The parser, data model, and normalization logic are identical whether the payload comes from a real API or a fixture file.

**What would be needed to add it:** A `DataSource.config` JSONField on each DataSource stores the API base URL, client ID, and token endpoint. The ingestion view would need an OAuth2 client (e.g., `requests-oauthlib`) to fetch a bearer token before calling the OData endpoint. This is a one-day addition once credentials are available.

---

## 2. No Celery async processing — ingestion is synchronous

**What was skipped:** The `requirements.txt` includes Celery and Redis, and `CELERY_BROKER_URL` is configured in settings. However, all three ingestion endpoints (`/api/ingest/sap/`, `/api/ingest/utility/`, `/api/ingest/travel/`) process records synchronously inside the HTTP request.

**Why it was skipped:** For the sample data sizes (10–15 SAP rows, 6 utility rows, 3 travel itineraries), synchronous processing completes in under 200ms. Async task infrastructure adds significant operational complexity — a separate Celery worker process and a Redis instance — that is not justified at this data volume. On Railway's free tier, running three services (web + worker + Redis) would exceed the free allowance.

**What breaks at scale:** A real SAP purchase order export for a year could contain 50,000+ line items. Processing those synchronously would cause the request to time out (Railway's default 30s request timeout). At that point, moving the `parser.parse()` call into a `shared_task` and returning a task ID immediately is the correct pattern. The `IngestionRun` model already has `status` and `records_created`/`records_failed` fields designed to be updated by an async task.

---

## 3. No SAP flat-file / IDoc / BAPI support — OData V4 JSON only

**What was skipped:** Real SAP environments expose procurement data through multiple export channels beyond OData REST APIs. The most common in enterprise deployments are:
- **IDoc (Intermediate Document):** SAP's native EDI format — a fixed-width, segment-based flat file (e.g., `ORDERS05`) used for system-to-system integration via ALE/EDI middleware.
- **BAPI flat-file export:** Finance and logistics teams frequently schedule batch jobs that dump purchase order data as pipe-delimited or comma-delimited CSV files to an SFTP server.
- **SAP Query / SE16 export:** Ad-hoc data extracts from SAP GUI saved as `.xlsx` or `.txt` files.

The current parser only accepts an OData V4 JSON payload (`{"value": [...]}` shape). If an organisation exports their SAP data as a CSV or IDoc, they cannot use the current ingestion endpoint without first converting the file.

**Why it was skipped:** Parsing IDoc requires either a custom fixed-width segment reader or a middleware adapter (e.g., MuleSoft, SAP PI/PO) — significant infrastructure that has nothing to do with emissions logic. CSV flat-file exports have no standardised column names across SAP versions or custom fields, meaning the parser would need a configurable column-mapping layer, which adds substantial UI and model complexity. OData V4 was chosen because it returns structured JSON with self-documenting field names (`Material`, `OrderQuantity`, `OrderQuantityUnit`) that map directly to the normalisation logic, and because SAP API Business Hub explicitly recommends OData V4 for new integrations.

**Concrete gap:** An analyst working at a company that only has SFTP-based batch exports from SAP ECC 6.0 (a common legacy version) cannot upload their data without a format conversion step. An IDoc `ORDERS05` message encodes the same quantity and material fields but in a completely different structure (e.g., `E1EDP01/MENGE` for quantity, `E1EDP09/WERKS` for plant).

**What would be needed to add it:** A CSV flat-file parser would require a configurable `ColumnMapping` model (user specifies which CSV column maps to `Material`, `OrderQuantity`, etc.) plus a file-upload endpoint that accepts `.csv` in addition to `.json`. An IDoc parser would require a segment reader library (e.g., `python-idoc`) and a mapping from ORDERS05 segment paths to the same normalisation inputs. Both are one- to two-week additions; neither affects the emission factor logic.
