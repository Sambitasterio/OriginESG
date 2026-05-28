"""
SAP OData V4 parser — Purchase Order line items → NormalizedRecord (Scope 1).

Expected input shape (API_PURCHASEORDER_PROCESS_SRV):
{
    "@odata.context": "...",
    "value": [
        {
            "PurchaseOrder":     "4500000001",
            "PurchaseOrderItem": "00010",
            "Material":          "DIESEL",
            "Plant":             "PLANT_MH01",
            "OrderQuantity":     "500.000",
            "OrderQuantityUnit": "L",
            "DocumentDate":      "2024-01-15",
            "Supplier":          "VENDOR001"
        },
        ...
    ]
}
"""

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ingestion.models import IngestionRun, NormalizedRecord, RawRecord
from ingestion.parsers.constants import (
    DEFRA_2023,
    EMISSION_FACTOR_SOURCE,
    FUEL_DENSITY_KG_PER_L,
    TO_LITRES,
)

logger = logging.getLogger(__name__)


class SAPParseError(Exception):
    pass


class SAPParser:
    def parse(self, payload: dict, ingestion_run: IngestionRun) -> dict:
        """
        Parse a full OData V4 response dict.
        Returns {"created": int, "failed": int, "errors": list[str]}.
        """
        records = payload.get("value", [])
        if not records:
            raise SAPParseError("OData payload has no 'value' array.")

        created = 0
        failed = 0
        errors = []

        for item in records:
            row_id = f"{item.get('PurchaseOrder', '')}-{item.get('PurchaseOrderItem', '')}"
            try:
                raw = RawRecord.objects.create(
                    ingestion_run=ingestion_run,
                    source_row_id=row_id,
                    raw_data=item,
                )
                self._normalize(raw, item)
                created += 1
            except Exception as exc:
                failed += 1
                msg = f"Row {row_id}: {exc}"
                errors.append(msg)
                logger.warning("SAP parse error — %s", msg)

        return {"created": created, "failed": failed, "errors": errors}

    # ── private ───────────────────────────────────────────────────────────────

    def _normalize(self, raw: RawRecord, item: dict) -> NormalizedRecord:
        material = (item.get("Material") or "").upper().strip()
        unit = (item.get("OrderQuantityUnit") or "").upper().strip()
        quantity_raw = item.get("OrderQuantity", "")
        doc_date = self._parse_date(item.get("DocumentDate"))

        # Validate required fields
        if not material:
            raise SAPParseError("Missing Material field.")
        if not unit:
            raise SAPParseError(
                f"Missing OrderQuantityUnit for material '{material}'. "
                "Cannot normalize without a unit."
            )

        try:
            original_value = Decimal(str(quantity_raw))
        except InvalidOperation:
            raise SAPParseError(f"Invalid OrderQuantity value: '{quantity_raw}'.")

        litres = self._to_litres(original_value, unit, material)
        factor = self._emission_factor(material)
        co2e = litres * factor

        return NormalizedRecord.objects.create(
            raw_record=raw,
            original_value=original_value,
            original_unit=unit,
            normalized_value=round(co2e, 6),
            normalized_unit="kg_CO2e",
            ghg_scope=NormalizedRecord.GHGScope.SCOPE_1,
            activity_type=f"fuel_combustion_{material.lower()}",
            emission_factor_used=factor,
            emission_factor_source=EMISSION_FACTOR_SOURCE,
            period_start=doc_date,
            period_end=doc_date,
        )

    def _to_litres(self, quantity: Decimal, unit: str, material: str) -> Decimal:
        if unit in TO_LITRES:
            return quantity * Decimal(str(TO_LITRES[unit]))

        # Mass unit — convert via fuel density
        if unit == "KG":
            density = FUEL_DENSITY_KG_PER_L.get(material)
            if density is None:
                raise SAPParseError(
                    f"Unit is KG but no density known for material '{material}'. "
                    "Cannot convert to litres."
                )
            return quantity / Decimal(str(density))

        raise SAPParseError(
            f"Unknown unit '{unit}'. Cannot convert to litres."
        )

    def _emission_factor(self, material: str) -> Decimal:
        factor = DEFRA_2023.get(material)
        if factor is None:
            raise SAPParseError(
                f"No DEFRA 2023 emission factor for material '{material}'. "
                "Add it to constants.py or exclude this material."
            )
        return Decimal(str(factor))

    def _parse_date(self, value) -> date | None:
        if not value:
            return None
        if isinstance(value, date):
            return value
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        logger.warning("SAP: could not parse DocumentDate '%s', storing null.", value)
        return None
