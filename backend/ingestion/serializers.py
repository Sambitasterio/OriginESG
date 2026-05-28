from rest_framework import serializers

from review.serializers import ReviewActionSerializer

from .models import IngestionRun, NormalizedRecord, RawRecord


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ["id", "source_row_id", "raw_data", "created_at"]


class NormalizedRecordListSerializer(serializers.ModelSerializer):
    source_type = serializers.CharField(
        source="raw_record.ingestion_run.data_source.source_type", read_only=True
    )
    run_id = serializers.IntegerField(source="raw_record.ingestion_run.id", read_only=True)

    class Meta:
        model = NormalizedRecord
        fields = [
            "id", "ghg_scope", "activity_type",
            "original_value", "original_unit",
            "normalized_value", "normalized_unit",
            "emission_factor_source", "status",
            "period_start", "period_end",
            "source_type", "run_id", "created_at",
        ]


class NormalizedRecordDetailSerializer(serializers.ModelSerializer):
    raw = RawRecordSerializer(source="raw_record", read_only=True)
    review_actions = ReviewActionSerializer(many=True, read_only=True)
    source_type = serializers.CharField(
        source="raw_record.ingestion_run.data_source.source_type", read_only=True
    )
    run_id = serializers.IntegerField(source="raw_record.ingestion_run.id", read_only=True)

    class Meta:
        model = NormalizedRecord
        fields = [
            "id", "ghg_scope", "activity_type",
            "original_value", "original_unit",
            "normalized_value", "normalized_unit",
            "emission_factor_used", "emission_factor_source",
            "status", "period_start", "period_end",
            "source_type", "run_id",
            "created_at", "updated_at",
            "raw", "review_actions",
        ]


class IngestionRunSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="data_source.name", read_only=True)
    source_type = serializers.CharField(source="data_source.source_type", read_only=True)

    class Meta:
        model = IngestionRun
        fields = [
            "id", "source_name", "source_type", "status",
            "records_created", "records_failed", "error_log",
            "started_at", "completed_at",
        ]
