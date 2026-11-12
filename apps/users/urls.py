"""Auth URLs - mounted at /api/v1/auth/ - API-001..API-004."""
from django.urls import path
from .views import RegisterView, LoginView, LogoutView, ProfileView

urlpatterns = [
    path('register', RegisterView.as_view(), name='auth-register'),
    path('login', LoginView.as_view(), name='auth-login'),
    path('logout', LogoutView.as_view(), name='auth-logout'),
    path('profile', ProfileView.as_view(), name='auth-profile'),
]
