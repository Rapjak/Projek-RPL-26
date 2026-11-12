"""Admin panel URLs - API-016..API-019."""
from django.urls import path
from .views import (
    AdminDashboardView, AdminActivitiesView,
    AdminRewardView, AdminRewardDetailView,
    AdminEducationView, AdminEducationDetailView,
)

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('activities/', AdminActivitiesView.as_view(), name='admin-activities'),
    path('rewards/', AdminRewardView.as_view(), name='admin-rewards'),
    path('rewards/<uuid:reward_id>/', AdminRewardDetailView.as_view(), name='admin-reward-detail'),
    path('education/', AdminEducationView.as_view(), name='admin-education'),
    path('education/<uuid:edu_id>/', AdminEducationDetailView.as_view(), name='admin-education-detail'),
]
