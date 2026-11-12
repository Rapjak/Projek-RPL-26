"""
URL configuration for config project - aligned to API-001..API-019 spec.

Primary prefix: /api/v1/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Pilah.in API",
        default_version='v1',
        description="API documentation for Pilah.in garbage classification app",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT token refresh (login/logout use custom views under /auth/)
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Authentication (API-001..API-004) - register/login/logout/profile
    path('api/v1/auth/', include('apps.users.urls')),

    # User profile/points (API-004, API-009)
    path('api/v1/', include('apps.users.profile_urls')),

    # Classifications (API-005..API-008) - POST upload, GET history, GET status, GET points
    path('api/v1/classifications/', include('apps.classifications.urls')),

    # Gamification (API-010..API-013) + leaderboard (API-011)
    path('api/v1/', include('apps.rewards.urls')),

    # Education (API-014, API-015)
    path('api/v1/education/', include('apps.education.urls')),

    # Admin / monitoring (API-016..API-019)
    path('api/v1/admin/', include('apps.admin_panel.urls')),

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
