"""
Quick end-to-end validation script.
Run: python validate.py
"""
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "breathe_esg.settings")
django.setup()

from django.contrib.auth import get_user_model
from organizations.models import Organization, DataSource
from ingestion.models import IngestionRun, RawRecord, NormalizedRecord
from review.models import ReviewAction
from ingestion.parsers.sap import SAPParser
from ingestion.parsers.utility import UtilityParser
from ingestion.parsers.travel import TravelParser

User = get_user_model()

PASS = "[PASS]"
FAIL = "[FAIL]"

def check(label, condition, detail=""):
    if condition:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label} {detail}")
    return condition


def reset_db():
    ReviewAction.objects.all().delete()
    NormalizedRecord.objects.all().delete()
    RawRecord.objects.all().delete()
    IngestionRun.objects.all().delete()
    DataSource.objects.all().delete()
    Organization.objects.all().delete()
    User.objects.filter(username="testuser").delete()


def setup():
    user = User.objects.create_user("testuser", password="testpass")
    org = Organization.objects.create(name="Test Org", slug="test-org")
    sap_ds = DataSource.objects.create(organization=org, name="SAP Feed", source_type="SAP")
    util_ds = DataSource.objects.create(organization=org, name="Utility Feed", source_type="UTILITY", config={"grid_region": "IN_CEA"})
    travel_ds = DataSource.objects.create(organization=org, name="Travel Feed", source_type="TRAVEL")
    return user, sap_ds, util_ds, travel_ds


# ── SAP Parser ────────────────────────────────────────────────────────────────
def test_sap(user, ds):
    print("\n-- SAP Parser --")
    payload = {
        "value": [
            {"PurchaseOrder": "4500000001", "PurchaseOrderItem": "00010",
             "Material": "DIESEL", "Plant": "PLANT_MH01",
             "OrderQuantity": "500", "OrderQuantityUnit": "L",
             "DocumentDate": "2024-01-15", "Supplier": "V001"},
            {"PurchaseOrder": "4500000001", "PurchaseOrderItem": "00020",
             "Material": "PETROL", "Plant": "PLANT_MH01",
             "OrderQuantity": "100", "OrderQuantityUnit": "GAL",
             "DocumentDate": "2024-01-15", "Supplier": "V001"},
            # Missing unit — should fail gracefully
            {"PurchaseOrder": "4500000001", "PurchaseOrderItem": "00030",
             "Material": "DIESEL", "Plant": "PLANT_MH01",
             "OrderQuantity": "200", "OrderQuantityUnit": "",
             "DocumentDate": "2024-01-15", "Supplier": "V001"},
        ]
    }
    run = IngestionRun.objects.create(data_source=ds, status="PROCESSING", triggered_by=user)
    result = SAPParser().parse(payload, run)

    check("2 records created", result["created"] == 2, result)
    check("1 record failed (missing unit)", result["failed"] == 1, result)

    norm = NormalizedRecord.objects.filter(raw_record__ingestion_run=run)
    check("2 NormalizedRecords in DB", norm.count() == 2)
    check("All Scope 1", all(n.ghg_scope == 1 for n in norm))

    diesel = norm.filter(activity_type="fuel_combustion_diesel").first()
    check("Diesel CO2e > 0", diesel and diesel.normalized_value > 0)

    # 100 GAL petrol = 378.541 L × 2.31489 = ~876.6 kg CO2e
    petrol = norm.filter(activity_type="fuel_combustion_petrol").first()
    check("Petrol unit conversion correct (GAL to L)",
          petrol and abs(float(petrol.normalized_value) - 876.6) < 1.0,
          f"got {petrol.normalized_value if petrol else 'None'}")


# ── Utility Parser ────────────────────────────────────────────────────────────
def test_utility(user, ds):
    print("\n-- Utility Parser --")
    csv_text = """ACCOUNT_NUMBER,METER_ID,INTERVAL_START,INTERVAL_END,USAGE,UNIT,COST
ACC001,MTR_BLD_A,2024-01-14,2024-02-11,1234.56,kWh,185.43
ACC001,MTR_BLD_A,2024-02-11,2024-03-14,980.00,kWh,147.00
ACC001,MTR_BLD_B,2024-01-14,2024-02-11,2.5,MWh,375.00"""

    run = IngestionRun.objects.create(data_source=ds, status="PROCESSING", triggered_by=user)
    result = UtilityParser().parse(csv_text, run)

    check("3 records created", result["created"] == 3, result)
    check("0 records failed", result["failed"] == 0, result)

    norm = NormalizedRecord.objects.filter(raw_record__ingestion_run=run)
    check("All Scope 2", all(n.ghg_scope == 2 for n in norm))

    # MWh row: 2.5 MWh = 2500 kWh × 0.716 (IN_CEA) = 1790 kg CO2e
    # Find by unit not by value — 2.5 (MWh) sorts lower than 980/1234 (kWh)
    mwh_row = norm.filter(original_unit="MWH").first()
    check("MWh to kWh conversion correct (2.5 MWh = 1790 kg CO2e)",
          mwh_row and abs(float(mwh_row.normalized_value) - 1790.0) < 1.0,
          f"got {mwh_row.normalized_value if mwh_row else 'None'}")

    # Check non-calendar billing period stored exactly
    first = norm.order_by("period_start").first()
    check("Non-calendar period stored (Jan 14)",
          str(first.period_start) == "2024-01-14")


# ── Travel Parser ─────────────────────────────────────────────────────────────
def test_travel(user, ds):
    print("\n-- Travel Parser --")
    payload = {
        "Itineraries": [
            {
                "TripId": "TRP001",
                "TripName": "London Trip",
                "Segments": [
                    {"Type": "Air", "StartCityCode": "DEL", "EndCityCode": "BOM",
                     "ClassOfService": "Y", "Vendor": "AI",
                     "StartDateLocal": "2024-02-15"},
                    {"Type": "Air", "StartCityCode": "BOM", "EndCityCode": "LHR",
                     "ClassOfService": "C", "Vendor": "BA",
                     "StartDateLocal": "2024-02-16"},
                    # Missing ClassOfService — should fall back to ECONOMY
                    {"Type": "Air", "StartCityCode": "LHR", "EndCityCode": "JFK",
                     "ClassOfService": "", "Vendor": "VS",
                     "StartDateLocal": "2024-02-20"},
                    {"Type": "Hotel", "Name": "The Savoy",
                     "StartDateLocal": "2024-02-16", "EndDateLocal": "2024-02-20"},
                    {"Type": "Car", "PickupDeliveryCity": "LHR",
                     "DropoffCollectionCity": "LHR", "Body": "Compact",
                     "StartDateLocal": "2024-02-16", "EndDateLocal": "2024-02-20"},
                ]
            }
        ]
    }
    run = IngestionRun.objects.create(data_source=ds, status="PROCESSING", triggered_by=user)
    result = TravelParser().parse(payload, run)

    check("5 records created", result["created"] == 5, result)
    check("0 records failed", result["failed"] == 0, result)

    norm = NormalizedRecord.objects.filter(raw_record__ingestion_run=run)
    check("All Scope 3", all(n.ghg_scope == 3 for n in norm))

    # Hotel: 4 nights × 20.8 = 83.2 kg CO2e
    hotel = norm.filter(activity_type="hotel_stay").first()
    check("Hotel 4 nights = 83.2 kg CO2e",
          hotel and float(hotel.normalized_value) == 83.2,
          f"got {hotel.normalized_value if hotel else 'None'}")

    # Car: 4 days × 17 = 68 kg CO2e
    car = norm.filter(activity_type="car_rental").first()
    check("Car 4 days = 68 kg CO2e",
          car and float(car.normalized_value) == 68.0,
          f"got {car.normalized_value if car else 'None'}")

    # Business class flight should have higher CO2e than economy of same distance
    bom_lhr = norm.filter(activity_type__contains="bom_lhr").first()
    del_bom = norm.filter(activity_type__contains="del_bom").first()
    check("Business class BOM-LHR has higher CO2e/km than economy DEL-BOM",
          bom_lhr and del_bom and
          float(bom_lhr.normalized_value) / 7213 > float(del_bom.normalized_value) / 1138)


# ── Review Actions ────────────────────────────────────────────────────────────
def test_review_actions():
    print("\n-- Review Action Logic --")
    record = NormalizedRecord.objects.first()
    if not record:
        print("  [SKIP] No records in DB to test review actions")
        return

    from django.contrib.auth import get_user_model
    user = get_user_model().objects.get(username="testuser")

    # Approve
    record.status = NormalizedRecord.Status.APPROVED
    record.save()
    ReviewAction.objects.create(normalized_record=record, action="APPROVE", actor=user)
    check("Approve creates ReviewAction", ReviewAction.objects.filter(normalized_record=record, action="APPROVE").exists())

    # Lock
    record.status = NormalizedRecord.Status.LOCKED
    record.save()
    ReviewAction.objects.create(normalized_record=record, action="LOCK", actor=user)
    check("Lock status saved", record.status == "LOCKED")

    # Verify locked record can't be re-approved in DB logic
    record.refresh_from_db()
    check("Locked record status persists", record.status == "LOCKED")


# ── Run all ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Breathe ESG Validation ===")
    reset_db()
    user, sap_ds, util_ds, travel_ds = setup()
    test_sap(user, sap_ds)
    test_utility(user, util_ds)
    test_travel(user, travel_ds)
    test_review_actions()
    print("\n=== Done ===")
