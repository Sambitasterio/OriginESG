from rest_framework import serializers
from .models import DataSource, Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug"]


class DataSourceSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = DataSource
        fields = ["id", "name", "source_type", "organization_name", "is_active"]
