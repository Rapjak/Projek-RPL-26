"""
Views for users app - implements API-001..API-004.

- API-001 POST /api/v1/auth/register  -> Register (role forced civitas)
- API-002 POST /api/v1/auth/login     -> Login (identifier = npm_nip OR email)
- API-003 POST /api/v1/auth/logout    -> Logout with blacklist
- API-004 GET  /api/v1/auth/profile   -> Retrieve profile
          PUT  /api/v1/auth/profile   -> Update profile
"""
import logging
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.utils.cache import get_user_cache_key
from .serializers import (
    UserRegisterSerializer,
    UserSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def _build_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'token_type': 'Bearer',
    }


class RegisterView(generics.CreateAPIView):
    """API-001: Register civitas account. Role cannot be injected (TC-006)."""
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'message': 'Registrasi berhasil',
            'user_id': str(user.id),
            'peran': user.role,
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """API-002: Login with npm_nip or email. Returns JWT + user payload."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    # Brute-force protection: 5 failed attempts / 60s per identifier (TC-011)
    MAX_ATTEMPTS = 5
    WINDOW_SECONDS = 60

    def _get_attempt_key(self, identifier):
        return f'login_attempts:{identifier.lower()}'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            identifier = request.data.get('identifier', '').strip().lower()
            if identifier:
                key = self._get_attempt_key(identifier)
                try:
                    attempts = (cache.get(key) or 0) + 1
                    cache.set(key, attempts, self.WINDOW_SECONDS)
                    # BVA: 5 failed attempts tolerated (401), 6th triggers 429 (lockout)
                    if attempts > self.MAX_ATTEMPTS:
                        return Response(
                            {'error': {'code': 'ERR_TOO_MANY_ATTEMPTS',
                                        'message': 'Terlalu banyak percobaan login. Coba lagi dalam 60 detik.'}},
                            status=status.HTTP_429_TOO_MANY_REQUESTS,
                            headers={'Retry-After': str(self.WINDOW_SECONDS)},
                        )
                except Exception as e:
                    logger.warning(f"Rate limit cache error: {e}")
            # Return uniform error (TC-009)
            return Response(
                {'error': {'code': 'ERR_INVALID_CREDENTIALS',
                            'message': 'NPM/NIP/Email atau kata sandi tidak valid'}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = serializer.validated_data['user']

        # Clear failed attempt counter on success
        identifier = request.data.get('identifier', '').strip().lower()
        try:
            cache.delete(self._get_attempt_key(identifier))
        except Exception:
            pass

        # Ensure JWT generation uses our custom claims
        tokens = _build_tokens(user)
        logger.info(f"User logged in: {user.email} (role: {user.role})")

        return Response({
            **tokens,
            'user': {
                'user_id': str(user.id),
                'npm_nip': user.npm_nip,
                'name': user.name,
                'email': user.email,
                'peran': user.role,
                'unit_gedung': user.unit_gedung,
                'total_poin': user.total_poin,
            },
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """API-003: Logout and blacklist token in Redis so it can't be reused (TC-012)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Blacklist the refresh token (so refresh rotation stops)
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError as e:
                logger.warning(f"Logout token error: {e}")

        # Also blacklist the access token's jti so subsequent requests with the
        # SAME access token are rejected (TC-012). We use Redis to do this since
        # SimpleJWT's OutstandingToken blacklist covers only refresh tokens.
        from django.core.cache import cache
        try:
            # request.auth is the validated token object (a dict-like)
            validated = request.auth
            if validated is not None:
                access_jti = validated.get('jti') if hasattr(validated, 'get') else None
                if access_jti:
                    exp = validated.get('exp')
                    import time
                    ttl = max(1, int(exp - time.time())) if exp else 3600
                    cache.set(f'jwt_blacklist:{access_jti}', 1, ttl)
        except Exception as e:
            logger.warning(f"Access token blacklist error: {e}")

        return Response({'message': 'Logout berhasil'}, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    """API-004: Retrieve or update current user profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return ProfileUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        try:
            cache.delete(get_user_cache_key(request.user.id, 'profile'))
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
        return super().update(request, *args, **kwargs)


class UserPointsView(APIView):
    """API-009: total points + rank."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # Rank = position by total_poin
        higher = User.objects.filter(total_poin__gt=user.total_poin).count()
        return Response({
            'user_id': str(user.id),
            'total_poin': user.total_poin,
            'rank': higher + 1,
        }, status=status.HTTP_200_OK)
