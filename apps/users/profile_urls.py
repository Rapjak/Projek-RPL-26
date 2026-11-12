"""User profile/points URLs - mounted at /api/v1/ - API-004, API-009."""
from django.urls import path
from .views import ProfileView, UserPointsView

urlpatterns = [
    path('profile', ProfileView.as_view(), name='user-profile'),
    path('points/me', UserPointsView.as_view(), name='user-points'),
]
