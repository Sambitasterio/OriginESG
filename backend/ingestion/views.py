import hashlib
from datetime import timezone as tz
from datetime import datetime

from django.db import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from review.models import ReviewAction

from .models import DataSource, IngestionRun, NormalizedRecord
from .parsers.sap import SAPParser, SAPParseError
from .parsers.travel import TravelParser, TravelParseError
from .parsers.utility import UtilityParser, UtilityParseError
from .serializers import IngestionRunSerializer


class IngestionRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        IngestionRun.objects
        .select_related("data_source__organization")
        .order_by("-started_at")
    )
    serializer_class = IngestionRunSerializer

    @action(detail=True, methods=["post"])
    def lock(self, request, pk=None):
        run = self.get_object()
        records = NormalizedRecord.objects.filter(
            raw_record__ingestion_run=run,
            status=NormalizedRecord.Status.APPROVED,
        )
        review_actions = []
        locked_ids = []
        for record in records:
            record.status = NormalizedRecord.Status.LOCKED
            record.save(update_fields=["status", "updated_at"])
            review_actions.append(
                ReviewAction(
                    normalized_record=record,
                    action=ReviewAction.Action.LOCK,
                    actor=request.user,
                )
            )
            locked_ids.append(record.id)
        ReviewAction.objects.bulk_create(review_actions)
        return Response({"locked": len(locked_ids), "ids": locked_ids})


# ── Ingest endpoints ──────────────────────────────────────────────────────────

def _get_data_source(data_source_id, expected_type):
    try:
        ds = DataSource.objects.get(pk=data_source_id, is_active=True)
    except DataSource.DoesNotExist:
        return None, Response(
            {"error": f"DataSource {data_source_id} not found or inactive."},
            status=status.HTTP_404_NOT_FOUND,
        )
    if ds.source_type != expected_type:
        return None, Response(
            {"error": f"DataSource {data_source_id} is type '{ds.source_type}', expected '{expected_type}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return ds, None


def _finish_run(run, result):
    run.status = (
        IngestionRun.Status.COMPLETE if result["failed"] == 0 else IngestionRun.Status.FAILED
    )
    run.records_created = result["created"]
    run.records_failed = result["failed"]
    run.error_log = "\n".join(result.get("errors", []))
    run.completed_at = datetime.now(tz.utc)
    run.save()


class IngestSAPView(APIView):
    """POST /api/ingest/sap/  — body: {data_source_id, payload: <OData V4 dict>}"""

    def post(self, request):
        data_source_id = request.data.get("data_source_id")
        payload = request.data.get("payload")
        if not data_source_id or not payload:
            return Response(
                {"error": "'data_source_id' and 'payload' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ds, err = _get_data_source(data_source_id, "SAP")
        if err:
            return err

        run = IngestionRun.objects.create(
            data_source=ds,
            status=IngestionRun.Status.PROCESSING,
            triggered_by=request.user,
        )
        try:
            result = SAPParser().parse(payload, run)
        except SAPParseError as exc:
            run.status = IngestionRun.Status.FAILED
            run.error_log = str(exc)
            run.completed_at = datetime.now(tz.utc)
            run.save()
            return Response({"error": str(exc), "run_id": run.id}, status=status.HTTP_400_BAD_REQUEST)

        _finish_run(run, result)
        return Response({**result, "run_id": run.id}, status=status.HTTP_201_CREATED)


class IngestUtilityView(APIView):
    """POST /api/ingest/utility/  — multipart: data_source_id + file (CSV)"""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        data_source_id = request.data.get("data_source_id")
        csv_file = request.FILES.get("file")
        if not data_source_id or not csv_file:
            return Response(
                {"error": "'data_source_id' and 'file' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ds, err = _get_data_source(data_source_id, "UTILITY")
        if err:
            return err

        csv_bytes = csv_file.read()
        file_hash = hashlib.sha256(csv_bytes).hexdigest()

        # Reject duplicate uploads
        if IngestionRun.objects.filter(file_hash=file_hash).exists():
            return Response(
                {"error": "This file has already been ingested (duplicate file hash)."},
                status=status.HTTP_409_CONFLICT,
            )

        run = IngestionRun.objects.create(
            data_source=ds,
            status=IngestionRun.Status.PROCESSING,
            file_hash=file_hash,
            triggered_by=request.user,
        )
        try:
            csv_text = csv_bytes.decode("utf-8")
            result = UtilityParser().parse(csv_text, run)
        except (UtilityParseError, UnicodeDecodeError) as exc:
            run.status = IngestionRun.Status.FAILED
            run.error_log = str(exc)
            run.completed_at = datetime.now(tz.utc)
            run.save()
            return Response({"error": str(exc), "run_id": run.id}, status=status.HTTP_400_BAD_REQUEST)

        _finish_run(run, result)
        return Response({**result, "run_id": run.id}, status=status.HTTP_201_CREATED)


class IngestTravelView(APIView):
    """POST /api/ingest/travel/  — body: {data_source_id, payload: <Concur Itinerary dict>}"""

    def post(self, request):
        data_source_id = request.data.get("data_source_id")
        payload = request.data.get("payload")
        if not data_source_id or not payload:
            return Response(
                {"error": "'data_source_id' and 'payload' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ds, err = _get_data_source(data_source_id, "TRAVEL")
        if err:
            return err

        run = IngestionRun.objects.create(
            data_source=ds,
            status=IngestionRun.Status.PROCESSING,
            triggered_by=request.user,
        )
        try:
            result = TravelParser().parse(payload, run)
        except TravelParseError as exc:
            run.status = IngestionRun.Status.FAILED
            run.error_log = str(exc)
            run.completed_at = datetime.now(tz.utc)
            run.save()
            return Response({"error": str(exc), "run_id": run.id}, status=status.HTTP_400_BAD_REQUEST)

        _finish_run(run, result)
        return Response({**result, "run_id": run.id}, status=status.HTTP_201_CREATED)
