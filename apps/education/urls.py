"""Education URLs - API-014, API-015, API-019."""
from django.urls import path
from .views import EducationMaterialListView, EducationMaterialDetailView

urlpatterns = [
    path('', EducationMaterialListView.as_view(), name='education-list'),
    path('<uuid:pk>/', EducationMaterialDetailView.as_view(), name='education-detail'),
]
