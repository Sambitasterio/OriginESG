"""
Green Button CSV parser — electricity interval data → NormalizedRecord (Scope 2).

Expected CSV columns (case-insensitive):
    ACCOUNT_NUMBER, METER_ID, INTERVAL_START, INTERVAL_END, USAGE, UNIT, COST (optional)

Example row:
    ACC001,MTR_BLD_A,2024-01-14,2024-02-11,1234.56,kWh,185.43

Key design decisions:
- Billing periods are stored exactly as they appear (may span 28–33 days).
  We never snap them to calendar months — that would misrepresent the data.
- The grid region emission factor is read from DataSource.config["grid_region"].
  If absent, we fall back to US_AVG and log a warning.
- MWh and GWh are converted to kWh before applying the factor.
"""

import csv
import io
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from ingestion.models import IngestionRun, NormalizedRecord, RawRecord
from ingestion.parsers.constants import (
    DEFAULT_GRID_REGION,
    EGRID_2023,
    EGRID_EMISSION_FACTOR_SOURCE,
    TO_KWH,
)

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"account_number", "meter_id", "interval_start", "interval_end", "usage", "unit"}

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S")


class UtilityParseError(Exception):
    pass


class UtilityParser:
    def parse(self, csv_text: str, ingestion_run: IngestionRun) -> dict:
        """
        Parse a Green Button CSV string.
        grid_region is read from ingestion_run.data_source.config.
        Returns {"created": int, "failed": int, "errors": list[str]}.
        """
        grid_region = (
            ingestion_run.data_source.config.get("grid_region", DEFAULT_GRID_REGION).upper()
        )
        if grid_region not in EGRID_2023:
            logger.warning(
                "Unknown grid region '%s', falling back to %s.", grid_region, DEFAULT_GRID_REGION
            )
            grid_region = DEFAULT_GRID_REGION

        emission_factor = Decimal(str(EGRID_2023[grid_region]))

        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        # Normalise header names to lowercase so column casing doesn't matter
        rows = [{k.lower().strip(): v.strip() for k, v in row.items()} for row in reader]

        if not rows:
            raise UtilityParseError("CSV file is empty or has no data rows.")

        missing = REQUIRED_COLUMNS - set(rows[0].keys())
        if missing:
            raise UtilityParseError(f"CSV missing required columns: {missing}")

        created = 0
        failed = 0
        errors = []

        for idx, row in enumerate(rows, start=2):  # start=2 because row 1 is header
            row_id = f"{row.get('meter_id', '?')}-row{idx}"
            try:
                raw = RawRecord.objects.create(
                    ingestion_run=ingestion_run,
                    source_row_id=row_id,
                    raw_data=row,
                )
                self._normalize(raw, row, emission_factor, grid_region)
                created += 1
            except Exception as exc:
                failed += 1
                msg = f"Row {idx}: {exc}"
                errors.append(msg)
                logger.warning("Utility parse error — %s", msg)

        return {"created": created, "failed": failed, "errors": errors}

    # ── private ───────────────────────────────────────────────────────────────

    def _normalize(self, raw: RawRecord, row: dict, emission_factor: Decimal, grid_region: str):
        unit = row.get("unit", "").upper().strip()
        usage_raw = row.get("usage", "")
        interval_start = self._parse_date(row.get("interval_start"), "interval_start")
        interval_end = self._parse_date(row.get("interval_end"), "interval_end")

        try:
            original_value = Decimal(str(usage_raw))
        except InvalidOperation:
            raise UtilityParseError(f"Invalid usage value: '{usage_raw}'.")

        if original_value < 0:
            raise UtilityParseError(f"Negative usage value '{original_value}' is not valid.")

        kwh = self._to_kwh(original_value, unit)
        co2e = kwh * emission_factor

        return NormalizedRecord.objects.create(
            raw_record=raw,
            original_value=original_value,
            original_unit=unit,
            normalized_value=round(co2e, 6),
            normalized_unit="kg_CO2e",
            ghg_scope=NormalizedRecord.GHGScope.SCOPE_2,
            activity_type=f"electricity_{grid_region.lower()}",
            emission_factor_used=emission_factor,
            emission_factor_source=f"{EGRID_EMISSION_FACTOR_SOURCE}_{grid_region}",
            period_start=interval_start,
            period_end=interval_end,
        )

    def _to_kwh(self, value: Decimal, unit: str) -> Decimal:
        multiplier = TO_KWH.get(unit)
        if multiplier is None:
            raise UtilityParseError(
                f"Unknown electricity unit '{unit}'. Expected one of: {list(TO_KWH.keys())}."
            )
        return value * Decimal(str(multiplier))

    def _parse_date(self, value, field_name: str):
        if not value:
            raise UtilityParseError(f"Missing required date field '{field_name}'.")
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise UtilityParseError(
            f"Cannot parse '{field_name}' value '{value}'. "
            f"Expected formats: YYYY-MM-DD or DD/MM/YYYY."
        )
