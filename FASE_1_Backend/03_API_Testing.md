# FASE 1 - Task 3: API Testing

## Metadata
- **Task**: API Testing with Django Test Framework
- **Date**: 2026-10-24
- **Status**: ✅ Completed
- **Developer**: AI Assistant

---

## 1. Tujuan Task
Implementasi unit tests dan integration tests untuk semua API endpoints dengan coverage:
- User authentication (register, login, token refresh)
- Profile management
- File upload flow
- Classification workflow
- Reward redemption system
- Education materials access

---

## 2. Test Structure

### 2.1 Directory Layout
```
Projek-RPL-26/
├── tests/
│   ├── __init__.py
│   ├── test_users.py
│   ├── test_uploads.py
│   ├── test_classifications.py
│   ├── test_rewards.py
│   └── test_education.py
```

---

## 3. Test Cases Summary

### 3.1 Users Tests (8 tests)
File: `tests/test_users.py`

| Test Class | Test Method | Description |
|------------|-------------|-------------|
| UserRegistrationTest | test_user_registration_success | Register dengan valid data |
| UserRegistrationTest | test_user_registration_password_mismatch | Password tidak cocok |
| UserRegistrationTest | test_user_registration_duplicate_email | Email sudah terdaftar |
| UserAuthenticationTest | test_token_obtain_success | Login berhasil |
| UserAuthenticationTest | test_token_obtain_wrong_password | Password salah |
| UserProfileTest | test_get_profile_authenticated | Get profile dengan token |
| UserProfileTest | test_get_profile_unauthenticated | Get profile tanpa token |
| UserProfileTest | test_update_profile | Update nama dan telepon |
| UserPointsTest | test_get_points | Get saldo poin |

### 3.2 Uploads Tests (3 tests)
File: `tests/test_uploads.py`

| Test Class | Test Method | Description |
|------------|-------------|-------------|
| UploadCreateTest | test_upload_create_authenticated | Upload dengan token |
| UploadCreateTest | test_upload_create_unauthenticated | Upload tanpa token |
| UploadListTest | test_list_user_uploads | List upload user |

### 3.3 Classifications Tests (3 tests)
File: `tests/test_classifications.py`

| Test Class | Test Method | Description |
|------------|-------------|-------------|
| ClassificationCreateTest | test_classification_create_authenticated | Trigger klasifikasi |
| ClassificationCreateTest | test_classification_create_unauthenticated | Klasifikasi tanpa token |
| ClassificationDetailTest | test_get_classification_detail | Get hasil klasifikasi |

### 3.4 Rewards Tests (5 tests)
File: `tests/test_rewards.py`

| Test Class | Test Method | Description |
|------------|-------------|-------------|
| RewardListTest | test_list_rewards | List rewards (public) |
| RewardRedemptionTest | test_redeem_reward_success | Redeem berhasil |
| RewardRedemptionTest | test_redeem_reward_insufficient_points | Poin tidak cukup |
| RewardRedemptionTest | test_redeem_reward_unauthenticated | Redeem tanpa token |
| PointTransactionTest | test_list_transactions | List riwayat poin |

### 3.5 Education Tests (4 tests)
File: `tests/test_education.py`

| Test Class | Test Method | Description |
|------------|-------------|-------------|
| EducationMaterialListTest | test_list_published_materials | List materi published |
| EducationMaterialListTest | test_unpublished_materials_not_visible | Unpublished tidak tampil |
| EducationMaterialDetailTest | test_get_material_detail | Get detail materi |

---

## 4. Test Implementation Details

### 4.1 Authentication Flow Testing
```python
# Create user
self.user = User.objects.create_user(
    email='test@example.com',
    name='Test User',
    password='TestPass123!'
)

# Generate JWT token
from rest_framework_simplejwt.tokens import RefreshToken
refresh = RefreshToken.for_user(self.user)
self.access_token = str(refresh.access_token)

# Set authorization header
self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
```

### 4.2 File Upload Testing
```python
def create_test_image(self):
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'png')
    file.seek(0)
    return SimpleUploadedFile('test.png', file.read(), content_type='image/png')
```

### 4.3 Permission Testing Pattern
```python
# Authenticated request
self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
response = self.client.get('/api/users/profile/')
self.assertEqual(response.status_code, status.HTTP_200_OK)

# Unauthenticated request
response = self.client.get('/api/users/profile/')
self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

---

## 5. Test Execution

### 5.1 Run All Tests
```bash
python manage.py test tests --verbosity=1
```

**Output:**
```
Found 23 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.......................
----------------------------------------------------------------------
Ran 23 tests in 4.943s

OK
```

### 5.2 Run Specific Test Module
```bash
python manage.py test tests.test_users
python manage.py test tests.test_uploads
python manage.py test tests.test_classifications
python manage.py test tests.test_rewards
python manage.py test tests.test_education
```

### 5.3 Run Specific Test Class
```bash
python manage.py test tests.test_users.UserRegistrationTest
```

---

## 6. Test Coverage by Endpoint

| Endpoint | Method | Tests |
|----------|--------|-------|
| /api/token/ | POST | Login success/fail |
| /api/users/register/ | POST | Register, duplicate, password mismatch |
| /api/users/profile/ | GET | Auth/Unauth |
| /api/users/profile/ | PUT | Update profile |
| /api/users/points/ | GET | Get points |
| /api/uploads/create/ | POST | Auth/Unauth |
| /api/uploads/ | GET | List uploads |
| /api/classifications/ | POST | Auth/Unauth |
| /api/classifications/<id>/ | GET | Get detail |
| /api/rewards/list/ | GET | List rewards |
| /api/rewards/redeem/ | POST | Success/Insufficient/Unauth |
| /api/rewards/transactions/ | GET | List transactions |
| /api/education/ | GET | List published/unpublished |
| /api/education/<id>/ | GET | Get detail |

---

## 7. Issues Fixed During Testing

### 7.1 Import Paths
**Problem**: Tests moved to project root couldn't import models with relative paths.
**Solution**: Changed `from .models import` to `from apps.<app>.models import`

### 7.2 UserDetailSerializer Email Field
**Problem**: PUT request failed with 400 because email was required but not sent.
**Solution**: Added 'email' to read_only_fields in UserDetailSerializer.

### 7.3 ClassificationDetailTest Upload Reference
**Problem**: `self.upload` referenced before creation via property.
**Solution**: Created upload in setUp() method directly.

---

## 8. Test Assertions Used

```python
# Status code
self.assertEqual(response.status_code, status.HTTP_201_CREATED)

# Database count
self.assertEqual(Upload.objects.count(), 1)

# Response data
self.assertEqual(response.data['points'], 100)
self.assertIn('access', response.data)

# Model refresh
self.user.refresh_from_db()
self.assertEqual(self.user.points, 50)
```

---

## 9. Test Database

Tests use separate test database:
- Created automatically before tests
- Destroyed after all tests complete
- Isolated from development database
- No data persistence between runs

---

## 10. Files Created

- `tests/__init__.py`
- `tests/test_users.py` - 8 tests
- `tests/test_uploads.py` - 3 tests
- `tests/test_classifications.py` - 3 tests
- `tests/test_rewards.py` - 5 tests
- `tests/test_education.py` - 4 tests

### Modified Files
- `apps/users/serializers.py` - Added email to read_only_fields

---

## 11. Checklist Completion

- [x] Create tests directory structure
- [x] Write user authentication tests
- [x] Write upload tests
- [x] Write classification tests
- [x] Write reward tests
- [x] Write education tests
- [x] Fix import paths
- [x] Fix serializer validation issues
- [x] Run all tests successfully
- [x] Create documentation

---

## 12. Test Results Summary

```
Total Tests: 23
Passed: 23
Failed: 0
Errors: 0
Execution Time: ~5 seconds
```

---

## 13. Next Steps

**FASE 2**: FastAPI ML Service
- Create FastAPI project structure
- Implement image classification endpoint
- Integrate with Django backend
- Add unit tests for ML service

---

## 14. Conclusion

Semua 23 API tests berhasil dijalankan. Testing coverage mencakup authentication flow, CRUD operations, permission checks, dan business logic. Backend siap untuk integration dengan FastAPI ML service di FASE 2.
