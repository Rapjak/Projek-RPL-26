"""
Classifications URLs - mounted at /api/v1/classifications/
Aligned to API-005, API-006, API-007, API-008.

Routes (parent include has trailing slash):
- POST /api/v1/classifications/              -> upload + classify (API-005)
- GET  /api/v1/classifications/              -> history list (API-007)
- GET  /api/v1/classifications/<id>/         -> poll status (API-006)
- GET  /api/v1/classifications/<id>/points/  -> check points (API-008)
"""
from django.urls import path
from apps.uploads.views import UploadCreateView, UploadDetailView, UploadListView
from .views import ClassificationPointsView

urlpatterns = [
    path('', UploadListView.as_view(), name='classification-list'),
    path('upload/', UploadCreateView.as_view(), name='classification-create'),
    path('<uuid:upload_id>/points/', ClassificationPointsView.as_view(), name='classification-points'),
    path('<uuid:upload_id>/', UploadDetailView.as_view(), name='classification-detail'),
]
