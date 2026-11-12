"""
Test suite for FR-001: Authentication
Covers TC-001..TC-012 (Registrasi, Login, Logout).
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .helpers import create_civitas_user, create_admin_user, auth_client, get_jwt_for

User = get_user_model()

REGISTER = '/api/v1/auth/register'
LOGIN = '/api/v1/auth/login'
LOGOUT = '/api/v1/auth/logout'
PROFILE = '/api/v1/auth/profile'


# ---------------------------------------------------------------------------
# TC-001..TC-006: Registration
# ---------------------------------------------------------------------------
class TC001_RegistrationSuccessTest(TestCase):
    """TC-001 - Normal registration with valid data."""

    def setUp(self):
        self.client = APIClient()

    def test_tc001_register_success(self):
        data = {
            'npm_nip': '140810240015',
            'name': 'Ahmad Dahlan',
            'email': 'ahmad@mail.unpad.ac.id',
            'unit_gedung': 'FMIPA',
            'password': 'Password123!',
        }
        r = self.client.post(REGISTER, data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['peran'], 'civitas')
        self.assertTrue(User.objects.filter(npm_nip='140810240015').exists())
        u = User.objects.get(npm_nip='140810240015')
        self.assertEqual(u.total_poin, 0)
        self.assertNotEqual(u.password, 'Password123!')  # hashed
        self.assertTrue(u.password.startswith(('pbkdf2', 'argon')))


class TC002_InvalidEmailTest(TestCase):
    """TC-002 - Email format invalid."""

    def setUp(self):
        self.client = APIClient()

    def test_tc002_invalid_email_rejected(self):
        data = {
            'npm_nip': '140810240015', 'name': 'Ahmad', 'email': 'ahmad_unpad.ac.id',
            'unit_gedung': 'FMIPA', 'password': 'Password123!',
        }
        r = self.client.post(REGISTER, data)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(npm_nip='140810240015').exists())


class TC003_DuplicateRegistrationTest(TestCase):
    """TC-003 - Duplicate email/NPM."""

    def setUp(self):
        self.client = APIClient()
        create_civitas_user(npm_nip='140810240015', email='ahmad@mail.unpad.ac.id')

    def test_tc003_duplicate_email(self):
        data = {
            'npm_nip': '140810240099', 'name': 'Other', 'email': 'ahmad@mail.unpad.ac.id',
            'unit_gedung': 'FMIPA', 'password': 'Password123!',
        }
        r = self.client.post(REGISTER, data)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tc003_duplicate_npm(self):
        data = {
            'npm_nip': '140810240015', 'name': 'Other', 'email': 'other@mail.unpad.ac.id',
            'unit_gedung': 'FMIPA', 'password': 'Password123!',
        }
        r = self.client.post(REGISTER, data)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class TC004_PasswordBelowMinimumTest(TestCase):
    """TC-004 - Password length 7 (BVA Min-1) should fail."""

    def setUp(self):
        self.client = APIClient()

    def test_tc004_short_password(self):
        data = {
            'npm_nip': '140810240015', 'name': 'Ahmad', 'email': 'ahmad@mail.unpad.ac.id',
            'unit_gedung': 'FMIPA', 'password': 'Abc123#',  # 7 chars
        }
        r = self.client.post(REGISTER, data)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class TC005_PasswordExactMinimumTest(TestCase):
    """TC-005 - Password length exactly 8 should succeed (BVA exactly Min)."""

    def setUp(self):
        self.client = APIClient()

    def test_tc005_password_min_8_chars(self):
        data = {
            'npm_nip': '140810240015', 'name': 'Ahmad', 'email': 'ahmad@mail.unpad.ac.id',
            'unit_gedung': 'FMIPA', 'password': 'Abcd123#',  # 8 chars
        }
        r = self.client.post(REGISTER, data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)


class TC006_RoleInjectionTest(TestCase):
    """TC-006 - Client tries to inject role=admin_gogreen via API payload."""

    def setUp(self):
        self.client = APIClient()

    def test_tc006_role_injection_blocked(self):
        data = {
            'npm_nip': '140810240015', 'name': 'Ahmad', 'email': 'ahmad@mail.unpad.ac.id',
            'unit_gedung': 'FMIPA', 'password': 'Password123!',
            'role': 'admin_gogreen',  # malicious payload
        }
        r = self.client.post(REGISTER, data)
        # Either rejected with 400 (if serializer enforces) or silently set to civitas (if ignored).
        # Our implementation: serializer doesn't include role field, so it gets ignored silently.
        if r.status_code == status.HTTP_201_CREATED:
            u = User.objects.get(npm_nip='140810240015')
            self.assertEqual(u.role, 'civitas')  # role MUST be civitas
        else:
            self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# TC-007..TC-011: Login
# ---------------------------------------------------------------------------
class TC007_LoginCivitasSuccessTest(TestCase):
    """TC-007 - Login civitas returns JWT + user payload."""

    def setUp(self):
        self.client = APIClient()
        create_civitas_user()

    def test_tc007_login_by_email(self):
        r = self.client.post(LOGIN, {'identifier': 'ahmad@mail.unpad.ac.id', 'password': 'Password123!'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', r.data)
        self.assertIn('refresh_token', r.data)
        self.assertEqual(r.data['user']['peran'], 'civitas')

    def test_tc007_login_by_npm(self):
        r = self.client.post(LOGIN, {'identifier': '140810240015', 'password': 'Password123!'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class TC008_LoginAdminRoutingTest(TestCase):
    """TC-008 - Admin login role routing (admin_gogreen should get admin role)."""

    def setUp(self):
        self.client = APIClient()
        create_admin_user()

    def test_tc008_admin_login(self):
        r = self.client.post(LOGIN, {'identifier': 'admin.gogreen@unpad.ac.id', 'password': 'AdminPass123!'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['user']['peran'], 'admin_gogreen')


class TC009_LoginInvalidCredentialsTest(TestCase):
    """TC-009 - Wrong password / unregistered account should give uniform error (no leak)."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = APIClient()
        create_civitas_user()

    def test_tc009_wrong_password(self):
        r = self.client.post(LOGIN, {'identifier': 'ahmad@mail.unpad.ac.id', 'password': 'PasswordSalahTotal!'})
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        # Uniform error code, no hint about whether email exists
        self.assertIn('ERR_INVALID_CREDENTIALS', str(r.data))

    def test_tc009_unregistered_user(self):
        r = self.client.post(LOGIN, {'identifier': 'tidakada@mail.unpad.ac.id', 'password': 'PasswordSalahTotal!'})
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class TC010_EmptyCredentialsTest(TestCase):
    """TC-010 - Empty / whitespace credentials."""

    def setUp(self):
        self.client = APIClient()

    def test_tc010_empty_both(self):
        r = self.client.post(LOGIN, {'identifier': '', 'password': ''})
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tc010_whitespace_only(self):
        r = self.client.post(LOGIN, {'identifier': '   ', 'password': '   '})
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class TC011_BruteForceRateLimitTest(TestCase):
    """TC-011 - 5 failed attempts tolerated, 6th returns 429 (BVA lockout)."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()  # ensure clean rate-limit state
        self.client = APIClient()
        create_civitas_user()

    def test_tc011_6th_attempt_locked(self):
        # Five failed attempts -> still 401, but counts toward lockout
        for i in range(5):
            r = self.client.post(LOGIN, {'identifier': 'ahmad@mail.unpad.ac.id', 'password': 'Wrong!'})
            self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        # Sixth attempt -> 429 Too Many Requests
        r = self.client.post(LOGIN, {'identifier': 'ahmad@mail.unpad.ac.id', 'password': 'Wrong!'})
        self.assertEqual(r.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


# ---------------------------------------------------------------------------
# TC-012: Logout + token blacklist
# ---------------------------------------------------------------------------
class TC012_LogoutTokenBlacklistTest(TestCase):
    """TC-012 - Logout blacklists JWT; subsequent profile request fails."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()  # ensure no stale blacklist entries
        self.client = APIClient()
        self.user = create_civitas_user()

    def test_tc012_logout_invalidates_token(self):
        client = auth_client(self.user)
        refresh = RefreshToken.for_user(self.user)
        # Sanity: profile works with valid token
        r = client.get(PROFILE)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        # Logout
        r = client.post(LOGOUT, {'refresh_token': str(refresh)})
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        # Subsequent request with the same token is rejected
        r = client.get(PROFILE)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        # Refresh token is in blacklist
        # We expect OutstandingToken + BlacklistedToken entries to exist for this user
        tokens = OutstandingToken.objects.filter(user=self.user)
        self.assertTrue(tokens.exists())
        self.assertTrue(BlacklistedToken.objects.filter(token__user=self.user).exists())
