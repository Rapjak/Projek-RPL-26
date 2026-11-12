# FASE 3: React Frontend Application

## Overview
FASE 3 builds React TypeScript frontend untuk Pilah.in garbage classification app, consuming Django REST API dari FASE 1 dan ML service dari FASE 2.

## Architecture
```
React App (Port 3000)
    ↓ HTTP/JSON
Django REST API (Port 8000)
    ↓
FastAPI ML Service (Port 8001)
    ↓
PostgreSQL + Redis
```

## Tech Stack
- **Framework**: React 18 + TypeScript + Vite
- **Build Tool**: Vite (faster than create-react-app)
- **Styling**: Tailwind CSS
- **State Management**: React Context API
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **Forms**: React Hook Form
- **UI Components**: Custom components + Headless UI
- **Icons**: Heroicons
- **Image Upload**: react-dropzone

## Project Structure
```
pilah-frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/         # Button, Input, Card, Modal
│   │   ├── layout/         # Header, Footer, Sidebar
│   │   └── features/       # Classification, Upload, Rewards
│   ├── pages/              # Route pages
│   │   ├── Home.tsx
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Upload.tsx
│   │   ├── History.tsx
│   │   ├── Rewards.tsx
│   │   ├── Education.tsx
│   │   └── Profile.tsx
│   ├── services/           # API integration
│   │   ├── api.ts          # Axios instance
│   │   ├── auth.ts         # Authentication API
│   │   ├── uploads.ts      # Upload API
│   │   ├── classifications.ts
│   │   ├── rewards.ts
│   │   └── education.ts
│   ├── context/            # React Context
│   │   ├── AuthContext.tsx
│   │   └── NotificationContext.tsx
│   ├── hooks/              # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   └── useNotification.ts
│   ├── types/              # TypeScript types
│   │   ├── auth.types.ts
│   │   ├── upload.types.ts
│   │   ├── classification.types.ts
│   │   └── reward.types.ts
│   ├── utils/              # Utility functions
│   │   ├── storage.ts      # localStorage wrapper
│   │   ├── formatters.ts   # Date, number formatters
│   │   └── validators.ts   # Form validation
│   ├── App.tsx
│   ├── index.tsx
│   └── routes.tsx
├── public/
├── .env
└── package.json
```

## Tasks

### Task 1: Project Setup
**Objective**: Initialize React TypeScript app with dependencies

**Steps**:
1. Create React app with TypeScript template
2. Install dependencies:
   - axios (HTTP client)
   - react-router-dom (routing)
   - tailwindcss (styling)
   - react-hook-form (forms)
   - @headlessui/react (UI components)
   - @heroicons/react (icons)
   - react-dropzone (file upload)
   - date-fns (date formatting)
3. Configure Tailwind CSS
4. Setup environment variables
5. Configure proxy to Django API

**Dependencies**:
```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "react-hook-form": "^7.48.0",
    "@headlessui/react": "^1.7.17",
    "@heroicons/react": "^2.0.18",
    "react-dropzone": "^14.2.3",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31"
  }
}
```

**Environment Variables** (`.env`):
```bash
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_APP_NAME=Pilah.in
```

### Task 2: API Service Layer
**Objective**: Create type-safe API client untuk Django backend

**Files**:
- `src/services/api.ts` - Axios instance with interceptors
- `src/services/auth.ts` - Authentication endpoints
- `src/services/uploads.ts` - Upload endpoints
- `src/services/classifications.ts` - Classification endpoints
- `src/services/rewards.ts` - Rewards endpoints
- `src/services/education.ts` - Education endpoints

**API Service Features**:
- Centralized Axios configuration
- JWT token injection
- Request/response interceptors
- Error handling
- Token refresh logic
- TypeScript interfaces

**Example** (`api.ts`):
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor - add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Task 3: Authentication System
**Objective**: Implement user authentication dengan JWT

**Components**:
- `pages/Login.tsx` - Login form
- `pages/Register.tsx` - Registration form
- `context/AuthContext.tsx` - Auth state management
- `hooks/useAuth.ts` - Auth hook

**Features**:
- User registration
- Email/password login
- JWT token storage
- Protected routes
- Auto-redirect on auth
- Logout functionality
- User profile loading

**Auth Flow**:
```
1. User enters credentials
2. POST /api/token/ → JWT tokens
3. Store tokens in localStorage
4. Set Authorization header
5. Redirect to dashboard
6. Load user profile
```

### Task 4: File Upload & Classification
**Objective**: Upload gambar dan request classification

**Components**:
- `pages/Upload.tsx` - Upload page with drag-drop
- `components/features/ImageUploader.tsx` - Dropzone component
- `components/features/ClassificationResult.tsx` - Result display

**Upload Flow**:
```
1. User selects/drops image
2. Validate file (type, size)
3. POST /api/uploads/create/ → Upload record
4. POST /api/classifications/ → Trigger ML classification
5. Poll or websocket for result
6. Display classification with:
   - Class name
   - Confidence score
   - Recyclability status
   - Handling instructions
   - Environmental impact
7. Show points earned
```

**Features**:
- Drag-and-drop upload
- Image preview
- File validation (JPEG/PNG, max 5MB)
- Upload progress
- Classification loading state
- Result visualization
- Points animation

### Task 5: Dashboard & History
**Objective**: User dashboard dengan upload history

**Components**:
- `pages/Dashboard.tsx` - Overview page
- `pages/History.tsx` - Classification history
- `components/features/StatCard.tsx` - Statistics display
- `components/features/HistoryTable.tsx` - History list

**Dashboard Sections**:
1. **Stats Cards**:
   - Total uploads
   - Total points
   - Classifications count
   - Recyclable percentage

2. **Recent Classifications**:
   - Last 5 classifications
   - Quick view with images

3. **Points Summary**:
   - Current balance
   - Points earned this month
   - Link to rewards page

4. **Quick Actions**:
   - Upload new image
   - View history
   - Browse rewards

**History Page**:
- Paginated list of all classifications
- Filters: date range, class type, recyclability
- Sorting: date, confidence, points
- Detail modal per classification
- Export to CSV option

### Task 6: Rewards System
**Objective**: Display rewards dan redemption

**Components**:
- `pages/Rewards.tsx` - Rewards catalog
- `components/features/RewardCard.tsx` - Single reward
- `components/features/TransactionHistory.tsx` - Point transactions

**Features**:
1. **Rewards Catalog**:
   - Grid layout
   - Filter by category
   - Sort by points/name
   - Show availability
   - Redeem button

2. **Redemption Modal**:
   - Confirm redemption
   - Show points deduction
   - Success/error feedback

3. **Transaction History**:
   - Earn transactions (classifications)
   - Spend transactions (redemptions)
   - Date and description
   - Running balance

**Reward Card Data**:
```typescript
interface Reward {
  id: string;
  name: string;
  description: string;
  points_required: number;
  category: string;
  image: string;
  stock: number;
  is_active: boolean;
}
```

### Task 7: Education Content
**Objective**: Display materi edukasi tentang waste management

**Components**:
- `pages/Education.tsx` - Education materials list
- `pages/EducationDetail.tsx` - Material detail page
- `components/features/MaterialCard.tsx` - Material preview

**Features**:
- List published materials
- Filter by category
- Search by title
- Material detail view with:
  - Title and description
  - Content (Markdown/HTML)
  - Related image
  - Categories
- Responsive layout

### Task 8: User Profile
**Objective**: User profile management

**Components**:
- `pages/Profile.tsx` - Profile page
- `components/features/ProfileForm.tsx` - Edit form
- `components/features/PointsCard.tsx` - Points display

**Features**:
1. **View Profile**:
   - Name, email, phone
   - Address
   - Points balance
   - Member since date

2. **Edit Profile**:
   - Update name, phone, address
   - Email not editable
   - Password change (future)
   - Form validation

3. **Statistics**:
   - Total classifications
   - Total points earned
   - Total rewards redeemed
   - Favorite waste type

### Task 9: Layout & Navigation
**Objective**: Consistent layout dengan navigation

**Components**:
- `components/layout/Header.tsx` - Top navigation
- `components/layout/Sidebar.tsx` - Side menu (mobile drawer)
- `components/layout/Footer.tsx` - Footer
- `components/common/ProtectedRoute.tsx` - Auth guard

**Header Features**:
- Logo and app name
- Navigation links
- User menu dropdown
- Points display
- Notifications (future)
- Logout button

**Navigation Links**:
- Dashboard
- Upload
- History
- Rewards
- Education
- Profile

### Task 10: Common Components
**Objective**: Reusable UI components

**Components**:
- `components/common/Button.tsx` - Button variants
- `components/common/Input.tsx` - Form input
- `components/common/Card.tsx` - Content card
- `components/common/Modal.tsx` - Modal dialog
- `components/common/Spinner.tsx` - Loading spinner
- `components/common/Alert.tsx` - Alert/notification
- `components/common/Badge.tsx` - Status badge
- `components/common/Table.tsx` - Data table

**Styling**:
- Tailwind CSS utility classes
- Consistent color scheme (green theme untuk eco-friendly)
- Responsive design (mobile-first)
- Accessibility (ARIA labels, keyboard navigation)

## API Integration Reference

### Authentication
```typescript
// POST /api/users/register/
register(data: { email, name, password, password2, phone?, address? })

// POST /api/token/
login(data: { email, password }) → { access, refresh }

// POST /api/token/refresh/
refreshToken(data: { refresh }) → { access }

// GET /api/users/profile/
getProfile() → User

// PUT /api/users/profile/
updateProfile(data: Partial<User>) → User

// GET /api/users/points/
getPoints() → { points }
```

### Uploads
```typescript
// POST /api/uploads/create/
createUpload(formData: FormData) → Upload

// GET /api/uploads/
listUploads(params?: { limit, offset, status }) → PaginatedUploads

// GET /api/uploads/{id}/
getUploadDetail(id: string) → Upload
```

### Classifications
```typescript
// POST /api/classifications/
createClassification(data: { upload_id }) → ClassificationResult

// GET /api/classifications/{id}/
getClassification(id: string) → ClassificationResult
```

### Rewards
```typescript
// GET /api/rewards/
listRewards(params?: { limit, offset, category }) → PaginatedRewards

// POST /api/rewards/redeem/
redeemReward(data: { reward_id }) → RewardRedemption

// GET /api/rewards/transactions/
getTransactions(params?: { limit, offset, type }) → PaginatedTransactions
```

### Education
```typescript
// GET /api/education/materials/
listMaterials(params?: { limit, offset, category }) → PaginatedMaterials

// GET /api/education/materials/{id}/
getMaterialDetail(id: string) → EducationMaterial
```

## Responsive Design Breakpoints
```css
/* Mobile first */
sm: 640px   /* Small devices */
md: 768px   /* Tablets */
lg: 1024px  /* Desktops */
xl: 1280px  /* Large desktops */
```

## Color Scheme (Tailwind)
```
Primary (Green): emerald-600, emerald-700
Secondary (Blue): blue-500, blue-600
Success: green-500
Warning: yellow-500
Error: red-500
Neutral: gray-100 to gray-900
```

## Testing Strategy
1. **Unit Tests**: Components with Jest + React Testing Library
2. **Integration Tests**: API service mocks
3. **E2E Tests**: Cypress (future)
4. **Manual Testing**: All user flows

## Deployment
1. **Build**: `npm run build`
2. **Output**: `build/` directory with static files
3. **Serve**: Deploy to Vercel/Netlify or serve via Django static files
4. **Environment**: Configure production API URL

## Implementation Sequence
1. ✅ Project setup (Task 1)
2. ✅ API service layer (Task 2)
3. ✅ Authentication (Task 3)
4. ✅ Common components (Task 10)
5. ✅ Layout & navigation (Task 9)
6. ✅ Dashboard (Task 5)
7. ✅ Upload & classification (Task 4)
8. ✅ History (Task 5)
9. ✅ Rewards (Task 6)
10. ✅ Education (Task 7)
11. ✅ Profile (Task 8)
12. ✅ Testing & refinement

## Next Steps
After FASE 3 completion:
- FASE 4: Production deployment
- FASE 5: Advanced features (real-time notifications, PWA, analytics)
