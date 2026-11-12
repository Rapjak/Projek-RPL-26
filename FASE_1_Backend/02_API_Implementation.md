# FASE 1 - Task 2: API Implementation

## Metadata
- **Task**: API Views, Serializers, URLs
- **Date**: 2026-10-24
- **Status**: ✅ Completed
- **Developer**: AI Assistant

---

## 1. Tujuan Task
Implementasi REST API endpoints untuk semua Django apps dengan fitur:
- JWT Authentication
- CRUD operations untuk semua models
- Swagger API documentation
- Admin panel registration

---

## 2. Serializers Implementation

### 2.1 Users App
File: `apps/users/serializers.py`

```python
- UserRegisterSerializer: Register dengan password validation
- UserSerializer: Basic user info
- UserDetailSerializer: Detailed user profile
```

### 2.2 Uploads App
File: `apps/uploads/serializers.py`

```python
- UploadSerializer: Upload file handling
- UploadDetailSerializer: Upload dengan classification result
```

### 2.3 Classifications App
File: `apps/classifications/serializers.py`

```python
- ClassificationResultSerializer: Classification result data
- ClassificationCreateSerializer: Trigger classification
```

### 2.4 Rewards App
File: `apps/rewards/serializers.py`

```python
- RewardSerializer: Reward catalog
- RewardRedemptionSerializer: Redemption history
- RewardRedemptionCreateSerializer: Redeem reward
- PointTransactionSerializer: Point history
```

### 2.5 Education App
File: `apps/education/serializers.py`

```python
- EducationMaterialSerializer: Full material
- EducationMaterialListSerializer: Material list preview
```

---

## 3. Views Implementation

### 3.1 Users Views
File: `apps/users/views.py`

| View | Method | Description |
|------|--------|-------------|
| UserRegisterView | POST | Register + auto JWT tokens |
| UserProfileView | GET/PUT | Get/update profile |
| UserPointsView | GET | Get current points |

### 3.2 Uploads Views
File: `apps/uploads/views.py`

| View | Method | Description |
|------|--------|-------------|
| UploadCreateView | POST | Upload image (MultiPartParser) |
| UploadListView | GET | List user uploads |
| UploadDetailView | GET | Upload detail + classification |

### 3.3 Classifications Views
File: `apps/classifications/views.py`

| View | Method | Description |
|------|--------|-------------|
| ClassificationCreateView | POST | Trigger classification (awards 10 points) |
| ClassificationDetailView | GET | Get classification result |

**Note**: Classification currently returns placeholder result. Will integrate with FastAPI ML service in FASE 2.

### 3.4 Rewards Views
File: `apps/rewards/views.py`

| View | Method | Description |
|------|--------|-------------|
| RewardListView | GET | List active rewards |
| RewardRedemptionCreateView | POST | Redeem reward (deducts points) |
| RewardRedemptionListView | GET | User redemption history |
| PointTransactionListView | GET | User point history |

### 3.5 Education Views
File: `apps/education/views.py`

| View | Method | Description |
|------|--------|-------------|
| EducationMaterialListView | GET | List published materials |
| EducationMaterialDetailView | GET | Material detail |

---

## 4. URL Configuration

### 4.1 Main URLs
File: `config/urls.py`

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
    path('api/token/verify/', TokenVerifyView.as_view()),
    
    # App URLs
    path('api/users/', include('apps.users.urls')),
    path('api/uploads/', include('apps.uploads.urls')),
    path('api/classifications/', include('apps.classifications.urls')),
    path('api/rewards/', include('apps.rewards.urls')),
    path('api/education/', include('apps.education.urls')),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger')),
    path('redoc/', schema_view.with_ui('redoc')),
]
```

### 4.2 App URLs

**Users**: `apps/users/urls.py`
```python
- register/
- profile/
- points/
```

**Uploads**: `apps/uploads/urls.py`
```python
- '' (list)
- create/
- <uuid:pk>/
```

**Classifications**: `apps/classifications/urls.py`
```python
- '' (create)
- <uuid:pk>/
```

**Rewards**: `apps/rewards/urls.py`
```python
- list/
- redeem/
- redemptions/
- transactions/
```

**Education**: `apps/education/urls.py`
```python
- '' (list)
- <uuid:pk>/
```

---

## 5. Admin Panel Registration

### 5.1 Users Admin
File: `apps/users/admin.py`
- UserAdmin: email, name, points, is_active, date_joined

### 5.2 Uploads Admin
File: `apps/uploads/admin.py`
- UploadAdmin: file_name, user, status, created_at

### 5.3 Classifications Admin
File: `apps/classifications/admin.py`
- ClassificationResultAdmin: class_name, confidence_score, is_recyclable

### 5.4 Rewards Admin
File: `apps/rewards/admin.py`
- RewardAdmin: name, points_required, stock, is_active
- RewardRedemptionAdmin: user, reward, status
- PointTransactionAdmin: user, points, transaction_type

### 5.5 Education Admin
File: `apps/education/admin.py`
- EducationMaterialAdmin: title, category, is_published

---

## 6. JWT Authentication Flow

### 6.1 Login
```bash
POST /api/token/
{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOi..."
}
```

### 6.2 Refresh Token
```bash
POST /api/token/refresh/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOi..."
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOi..."
}
```

### 6.3 Using Access Token
```bash
GET /api/users/profile/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOi...
```

---

## 7. API Endpoints Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/token/ | No | Login |
| POST | /api/token/refresh/ | No | Refresh token |
| POST | /api/users/register/ | No | Register |
| GET/PUT | /api/users/profile/ | Yes | Profile |
| GET | /api/users/points/ | Yes | Points |
| GET | /api/uploads/ | Yes | List uploads |
| POST | /api/uploads/create/ | Yes | Upload file |
| GET | /api/uploads/<id>/ | Yes | Upload detail |
| POST | /api/classifications/ | Yes | Classify |
| GET | /api/classifications/<id>/ | Yes | Result |
| GET | /api/rewards/list/ | No | Rewards |
| POST | /api/rewards/redeem/ | Yes | Redeem |
| GET | /api/rewards/redemptions/ | Yes | History |
| GET | /api/rewards/transactions/ | Yes | Points |
| GET | /api/education/ | No | Materials |
| GET | /api/education/<id>/ | No | Detail |
| GET | /swagger/ | No | API docs |

---

## 8. Permissions Configuration

| Endpoint Type | Permission |
|--------------|------------|
| Register, Login | AllowAny |
| Rewards List, Education | AllowAny |
| User Data, Uploads | IsAuthenticated |

---

## 9. Testing Commands

### 9.1 System Check
```bash
python manage.py check
```
**Output**: System check identified no issues (0 silenced).

### 9.2 Run Development Server
```bash
python manage.py runserver
```
Access:
- API: http://127.0.0.1:8000/api/
- Swagger: http://127.0.0.1:8000/swagger/
- Admin: http://127.0.0.1:8000/admin/

---

## 10. Files Created

### Serializers
- `apps/users/serializers.py`
- `apps/uploads/serializers.py`
- `apps/classifications/serializers.py`
- `apps/rewards/serializers.py`
- `apps/education/serializers.py`

### Views
- `apps/users/views.py`
- `apps/uploads/views.py`
- `apps/classifications/views.py`
- `apps/rewards/views.py`
- `apps/education/views.py`

### URLs
- `apps/users/urls.py`
- `apps/uploads/urls.py`
- `apps/classifications/urls.py`
- `apps/rewards/urls.py`
- `apps/education/urls.py`

### Admin
- `apps/users/admin.py`
- `apps/uploads/admin.py`
- `apps/classifications/admin.py`
- `apps/rewards/admin.py`
- `apps/education/admin.py`

### Modified
- `config/urls.py` - Added all routes + swagger
- `config/settings.py` - SECRET_KEY from env

---

## 11. Checklist Completion

- [x] Create serializers for all apps
- [x] Create views for all apps
- [x] Create URLs for all apps
- [x] Configure main URLs with JWT + Swagger
- [x] Register models in admin panel
- [x] Test system check
- [x] Create documentation

---

## 12. Next Steps

**FASE 1 Task 3**: Testing API dengan test cases
- Unit tests untuk views
- Integration tests untuk authentication
- Test file upload flow

---

## 13. Conclusion

REST API backend siap digunakan dengan 16 endpoints, JWT authentication, dan Swagger documentation. Semua models terdaftar di admin panel. Backend siap untuk integration dengan React frontend (FASE 3) dan FastAPI ML service (FASE 2).
