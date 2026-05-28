from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from ingestion.views import IngestionRunViewSet, IngestSAPView, IngestTravelView, IngestUtilityView
from organizations.views import DataSourceViewSet
from review.views import NormalizedRecordViewSet

router = DefaultRouter()
router.register(r"records", NormalizedRecordViewSet, basename="record")
router.register(r"runs", IngestionRunViewSet, basename="run")
router.register(r"datasources", DataSourceViewSet, basename="datasource")

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT auth
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Review + run endpoints
    path("api/", include(router.urls)),

    # Ingestion trigger endpoints
    path("api/ingest/sap/", IngestSAPView.as_view(), name="ingest_sap"),
    path("api/ingest/utility/", IngestUtilityView.as_view(), name="ingest_utility"),
    path("api/ingest/travel/", IngestTravelView.as_view(), name="ingest_travel"),

    # Railway health check
    path("api/health/", lambda r: JsonResponse({"status": "ok"}), name="health"),
]
