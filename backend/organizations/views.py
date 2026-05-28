from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import DataSource
from .serializers import DataSourceSerializer


class DataSourceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = DataSource.objects.filter(is_active=True).select_related("organization")
        source_type = self.request.query_params.get("source_type")
        if source_type:
            qs = qs.filter(source_type=source_type.upper())
        return qs
