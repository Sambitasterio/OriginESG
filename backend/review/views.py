from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ingestion.models import NormalizedRecord
from ingestion.serializers import (
    NormalizedRecordDetailSerializer,
    NormalizedRecordListSerializer,
)

from .models import ReviewAction


class NormalizedRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        NormalizedRecord.objects
        .select_related("raw_record__ingestion_run__data_source")
        .prefetch_related("review_actions__actor")
        .order_by("-created_at")
    )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return NormalizedRecordDetailSerializer
        return NormalizedRecordListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if s := params.get("status"):
            qs = qs.filter(status=s.upper())
        if scope := params.get("scope"):
            qs = qs.filter(ghg_scope=scope)
        if source_type := params.get("source_type"):
            qs = qs.filter(
                raw_record__ingestion_run__data_source__source_type=source_type.upper()
            )
        if run_id := params.get("run_id"):
            qs = qs.filter(raw_record__ingestion_run_id=run_id)
        return qs

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        record = self.get_object()
        if record.status == NormalizedRecord.Status.LOCKED:
            return Response(
                {"error": "Record is locked and cannot be modified."},
                status=status.HTTP_403_FORBIDDEN,
            )
        record.status = NormalizedRecord.Status.APPROVED
        record.save(update_fields=["status", "updated_at"])
        ReviewAction.objects.create(
            normalized_record=record,
            action=ReviewAction.Action.APPROVE,
            actor=request.user,
        )
        return Response({"id": record.id, "status": record.status})

    @action(detail=True, methods=["post"])
    def flag(self, request, pk=None):
        record = self.get_object()
        if record.status == NormalizedRecord.Status.LOCKED:
            return Response(
                {"error": "Record is locked and cannot be modified."},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment = request.data.get("comment", "")
        record.status = NormalizedRecord.Status.FLAGGED
        record.save(update_fields=["status", "updated_at"])
        ReviewAction.objects.create(
            normalized_record=record,
            action=ReviewAction.Action.FLAG,
            comment=comment,
            actor=request.user,
        )
        return Response({"id": record.id, "status": record.status})

    @action(detail=False, methods=["post"], url_path="batch-approve")
    def batch_approve(self, request):
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "'ids' list is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        records = (
            NormalizedRecord.objects
            .filter(id__in=ids)
            .exclude(status=NormalizedRecord.Status.LOCKED)
        )
        review_actions = []
        updated_ids = []
        for record in records:
            record.status = NormalizedRecord.Status.APPROVED
            record.save(update_fields=["status", "updated_at"])
            review_actions.append(
                ReviewAction(
                    normalized_record=record,
                    action=ReviewAction.Action.APPROVE,
                    actor=request.user,
                )
            )
            updated_ids.append(record.id)
        ReviewAction.objects.bulk_create(review_actions)
        return Response({"approved": len(updated_ids), "ids": updated_ids})
