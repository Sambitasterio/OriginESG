from django.contrib import admin
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def _reset_admin(request):
    if request.GET.get("secret") != "breathe-esg-reset-2026":
        return JsonResponse({"error": "forbidden"}, status=403)
    u, created = User.objects.get_or_create(
        username="sambit",
        defaults={"is_superuser": True, "is_staff": True, "email": "sambit.behera8587@gmail.com"},
    )
    u.set_password("Sambit@123")
    u.is_superuser = True
    u.is_staff = True
    u.save()
    u.refresh_from_db()
    ok = u.check_password("Sambit@123")
    return JsonResponse({"created": created, "verified": ok})

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

    # Temporary one-time password reset — remove after login works
    path("api/reset-admin/", _reset_admin),
]
