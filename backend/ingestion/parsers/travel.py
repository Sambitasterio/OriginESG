"""
Concur Itinerary API parser — flight/hotel/car segments → NormalizedRecord (Scope 3 Cat 6).

Expected input shape:
{
    "Itineraries": [
        {
            "TripId": "TRP001",
            "TripName": "Mumbai Business Trip",
            "Segments": [
                {
                    "Type": "Air",
                    "StartCityCode": "DEL",
                    "EndCityCode": "BOM",
                    "ClassOfService": "Y",
                    "Vendor": "AI",
                    "StartDateLocal": "2024-02-15T10:30:00"
                },
                {
                    "Type": "Hotel",
                    "Name": "Taj Mahal Palace",
                    "StartDateLocal": "2024-02-15",
                    "EndDateLocal": "2024-02-17",
                    "DailyRate": 250.0
                },
                {
                    "Type": "Car",
                    "PickupDeliveryCity": "BOM",
                    "DropoffCollectionCity": "BOM",
                    "Body": "Compact",
                    "Class": "CCAR",
                    "StartDateLocal": "2024-02-15",
                    "EndDateLocal": "2024-02-17"
                }
            ]
        }
    ]
}
"""

import logging
import math
from datetime import datetime
from decimal import Decimal

from ingestion.models import IngestionRun, NormalizedRecord, RawRecord
from ingestion.parsers.constants import (
    AIRPORT_COORDS,
    CAR_EMISSION_FACTOR_KG_PER_DAY,
    CONCUR_CLASS_MAP,
    DEFAULT_CABIN_CLASS,
    FLIGHT_CABIN_MULTIPLIERS,
    FLIGHT_EMISSION_FACTOR_KG_PER_PKM,
    HOTEL_EMISSION_FACTOR_KG_PER_NIGHT,
    TRAVEL_EMISSION_FACTOR_SOURCE,
)

logger = logging.getLogger(__name__)

DATE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y",
)


class TravelParseError(Exception):
    pass


class TravelParser:
    def parse(self, payload: dict, ingestion_run: IngestionRun) -> dict:
        """
        Parse a full Concur Itinerary API response.
        Returns {"created": int, "failed": int, "errors": list[str]}.
        """
        itineraries = payload.get("Itineraries", [])
        if not itineraries:
            raise TravelParseError("Payload has no 'Itineraries' array.")

        created = 0
        failed = 0
        errors = []

        for trip in itineraries:
            trip_id = trip.get("TripId", "unknown")
            for idx, segment in enumerate(trip.get("Segments", [])):
                seg_type = segment.get("Type", "").upper()
                row_id = f"{trip_id}-{seg_type}-{idx}"
                try:
                    raw = RawRecord.objects.create(
                        ingestion_run=ingestion_run,
                        source_row_id=row_id,
                        raw_data={**segment, "_trip_id": trip_id},
                    )
                    if seg_type == "AIR":
                        self._normalize_flight(raw, segment)
                    elif seg_type == "HOTEL":
                        self._normalize_hotel(raw, segment)
                    elif seg_type == "CAR":
                        self._normalize_car(raw, segment)
                    else:
                        raise TravelParseError(f"Unknown segment type '{seg_type}'.")
                    created += 1
                except Exception as exc:
                    failed += 1
                    msg = f"{row_id}: {exc}"
                    errors.append(msg)
                    logger.warning("Travel parse error — %s", msg)

        return {"created": created, "failed": failed, "errors": errors}

    # ── flights ───────────────────────────────────────────────────────────────

    def _normalize_flight(self, raw: RawRecord, segment: dict):
        origin = (segment.get("StartCityCode") or "").upper().strip()
        dest = (segment.get("EndCityCode") or "").upper().strip()
        cos = (segment.get("ClassOfService") or "").upper().strip()
        start_date = self._parse_date(segment.get("StartDateLocal"), "StartDateLocal")

        if not origin or not dest:
            raise TravelParseError("Flight segment missing StartCityCode or EndCityCode.")

        distance_km = self._great_circle_km(origin, dest)

        # Resolve cabin class — fall back to ECONOMY if code is missing or unknown
        if not cos:
            logger.warning(
                "Flight %s→%s has no ClassOfService; defaulting to %s.",
                origin, dest, DEFAULT_CABIN_CLASS,
            )
            cabin = DEFAULT_CABIN_CLASS
        else:
            cabin = CONCUR_CLASS_MAP.get(cos, DEFAULT_CABIN_CLASS)
            if cos not in CONCUR_CLASS_MAP:
                logger.warning(
                    "Unknown ClassOfService '%s' on %s→%s; defaulting to %s.",
                    cos, origin, dest, DEFAULT_CABIN_CLASS,
                )

        multiplier = FLIGHT_CABIN_MULTIPLIERS[cabin]
        factor = Decimal(str(FLIGHT_EMISSION_FACTOR_KG_PER_PKM)) * Decimal(str(multiplier))
        co2e = Decimal(str(distance_km)) * factor

        NormalizedRecord.objects.create(
            raw_record=raw,
            original_value=Decimal(str(distance_km)),
            original_unit="km",
            normalized_value=round(co2e, 6),
            normalized_unit="kg_CO2e",
            ghg_scope=NormalizedRecord.GHGScope.SCOPE_3,
            activity_type=f"flight_{cabin.lower()}_{origin.lower()}_{dest.lower()}",
            emission_factor_used=factor,
            emission_factor_source=f"{TRAVEL_EMISSION_FACTOR_SOURCE}_FLIGHT_{cabin}",
            period_start=start_date,
            period_end=start_date,
        )

    # ── hotels ────────────────────────────────────────────────────────────────

    def _normalize_hotel(self, raw: RawRecord, segment: dict):
        start = self._parse_date(segment.get("StartDateLocal"), "StartDateLocal")
        end = self._parse_date(segment.get("EndDateLocal"), "EndDateLocal")

        if not start or not end:
            raise TravelParseError("Hotel segment missing StartDateLocal or EndDateLocal.")
        if end <= start:
            raise TravelParseError(
                f"Hotel end date {end} is not after start date {start}."
            )

        nights = (end - start).days
        factor = Decimal(str(HOTEL_EMISSION_FACTOR_KG_PER_NIGHT))
        co2e = Decimal(nights) * factor

        NormalizedRecord.objects.create(
            raw_record=raw,
            original_value=Decimal(nights),
            original_unit="nights",
            normalized_value=round(co2e, 6),
            normalized_unit="kg_CO2e",
            ghg_scope=NormalizedRecord.GHGScope.SCOPE_3,
            activity_type="hotel_stay",
            emission_factor_used=factor,
            emission_factor_source=f"{TRAVEL_EMISSION_FACTOR_SOURCE}_HOTEL",
            period_start=start,
            period_end=end,
        )

    # ── cars ──────────────────────────────────────────────────────────────────

    def _normalize_car(self, raw: RawRecord, segment: dict):
        start = self._parse_date(segment.get("StartDateLocal"), "StartDateLocal")
        end = self._parse_date(segment.get("EndDateLocal"), "EndDateLocal")

        if not start or not end:
            raise TravelParseError("Car segment missing StartDateLocal or EndDateLocal.")
        if end < start:
            raise TravelParseError(
                f"Car end date {end} is before start date {start}."
            )

        # Same-day rental counts as 1 day
        days = max((end - start).days, 1)
        factor = Decimal(str(CAR_EMISSION_FACTOR_KG_PER_DAY))
        co2e = Decimal(days) * factor

        NormalizedRecord.objects.create(
            raw_record=raw,
            original_value=Decimal(days),
            original_unit="days",
            normalized_value=round(co2e, 6),
            normalized_unit="kg_CO2e",
            ghg_scope=NormalizedRecord.GHGScope.SCOPE_3,
            activity_type="car_rental",
            emission_factor_used=factor,
            emission_factor_source=f"{TRAVEL_EMISSION_FACTOR_SOURCE}_CAR",
            period_start=start,
            period_end=end,
        )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _great_circle_km(self, origin: str, dest: str) -> float:
        """
        Haversine great-circle distance between two IATA airport codes.
        Raises TravelParseError if either code is not in AIRPORT_COORDS.
        """
        if origin not in AIRPORT_COORDS:
            raise TravelParseError(
                f"Airport code '{origin}' not in known airports list. "
                "Add it to constants.AIRPORT_COORDS."
            )
        if dest not in AIRPORT_COORDS:
            raise TravelParseError(
                f"Airport code '{dest}' not in known airports list. "
                "Add it to constants.AIRPORT_COORDS."
            )

        lat1, lon1 = map(math.radians, AIRPORT_COORDS[origin])
        lat2, lon2 = map(math.radians, AIRPORT_COORDS[dest])

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 6371 * 2 * math.asin(math.sqrt(a))   # Earth radius = 6371 km

    def _parse_date(self, value, field_name: str):
        if not value:
            return None
        if hasattr(value, "date"):
            return value.date()
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(str(value), fmt).date()
            except ValueError:
                continue
        raise TravelParseError(
            f"Cannot parse '{field_name}' value '{value}'."
        )
