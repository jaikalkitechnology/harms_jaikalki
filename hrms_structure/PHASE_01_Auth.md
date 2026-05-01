# Phase 1: Authentication & RBAC

**Duration:** 5-7 days
**Hours:** 50
**Priority:** CRITICAL
**Depends on:** Phase 0 (Foundation)

---

## Objective

Build complete authentication system with JWT, refresh tokens, biometric support, and Role-Based Access Control (RBAC) with designation levels.

## Deliverables

- ✅ User registration & login working
- ✅ JWT access + refresh token system
- ✅ Permission-based access control
- ✅ 5 roles (Director, HR, Admin, Manager, Employee)
- ✅ Designation levels (L1-L5)
- ✅ Flutter login screen functional
- ✅ Biometric login (Face ID / Fingerprint)
- ✅ Role-based home routing

---

## Tasks

### Task 1.1: Database Models (6h)

Create models:

**`app/models/user.py`:**
- User (id, email, phone, password_hash, is_active, mfa_enabled, created_at)

**`app/models/role.py`:**
- Role (id, name, level, description)
- Permission (id, code, description, category)
- RolePermission (role_id, permission_id)
- UserRole (user_id, role_id, assigned_at)

**`app/models/designation.py`:**
- Designation (id, name, level, department_id)
- Department (id, name, head_id)

### Task 1.2: Alembic Migrations (3h)

```bash
alembic revision --autogenerate -m "Initial auth tables"
alembic upgrade head
```

### Task 1.3: Seed Data (3h)

Create `scripts/seed_auth.py`:

**Roles:**
- Director (level 5)
- HR (level 4)
- Admin (level 3)
- Manager (level 3)
- Employee (level 1)

**Permissions:**
- `employee.view.self`
- `employee.view.team`
- `employee.view.all`
- `salary.view.self`
- `salary.view.team`
- `salary.view.all`
- `leave.apply`
- `leave.approve.team`
- `payroll.run`
- (~30 permissions total)

**Default users:**
- `admin@hrms.com` / `admin123` (Director)
- `hr@hrms.com` / `hr123` (HR)
- `manager@hrms.com` / `manager123` (Manager)
- `employee@hrms.com` / `employee123` (Employee)

### Task 1.4: Security Module (4h)

`app/core/security.py`:
- Password hashing (bcrypt)
- JWT encode/decode
- Access token generation (15 min)
- Refresh token generation (30 days)
- Token validation
- Password verification

### Task 1.5: Auth Service (4h)

`app/services/auth_service.py`:
- `authenticate_user(email, password)`
- `create_tokens(user)`
- `refresh_token(refresh_token)`
- `logout(token)`
- `get_current_user(token)`

### Task 1.6: Permission System (4h)

`app/core/permissions.py`:
```python
@require_permission("salary.view.team")
@require_role("manager")
@require_level(3)
@require_scope("team")  # self/team/all
```

### Task 1.7: Auth API Endpoints (5h)

`app/api/v1/auth.py`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Email + password → tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Invalidate token |
| GET | `/auth/me` | Current user + permissions |
| POST | `/auth/forgot-password` | Send OTP |
| POST | `/auth/reset-password` | Reset with OTP |
| POST | `/auth/change-password` | Authenticated change |

### Task 1.8: Backend Tests (3h)

`tests/test_auth.py`:
- Login success
- Login wrong password
- Token refresh
- Permission check pass
- Permission check fail
- Role check
- Logout

### Task 1.9: Flutter - Auth Feature Folder (2h)

```
features/auth/
├── data/
│   ├── models/
│   │   ├── user_model.dart
│   │   └── auth_response_model.dart
│   ├── datasources/
│   │   └── auth_remote_datasource.dart
│   └── repositories/
│       └── auth_repository_impl.dart
├── domain/
│   ├── entities/
│   │   └── user.dart
│   ├── repositories/
│   │   └── auth_repository.dart
│   └── usecases/
│       ├── login.dart
│       ├── logout.dart
│       └── refresh_token.dart
└── presentation/
    ├── bloc/
    │   ├── auth_bloc.dart
    │   ├── auth_event.dart
    │   └── auth_state.dart
    ├── pages/
    │   ├── login_page.dart
    │   └── splash_page.dart
    └── widgets/
        ├── login_form.dart
        └── biometric_button.dart
```

### Task 1.10: Flutter - AuthBloc (4h)

States:
- `AuthInitial`
- `AuthLoading`
- `AuthAuthenticated(user, permissions, role, level)`
- `AuthUnauthenticated`
- `AuthError(message)`

Events:
- `AuthCheckRequested`
- `AuthLoginRequested(email, password)`
- `AuthBiometricLoginRequested`
- `AuthLogoutRequested`
- `AuthTokenRefreshRequested`

### Task 1.11: Flutter - Login Screen (4h)

Features:
- Email + password fields
- Show/hide password toggle
- Remember me checkbox
- Login button with loading state
- Biometric login button
- Forgot password link
- Form validation
- Error display

### Task 1.12: Flutter - Token Management (3h)

- Store tokens in flutter_secure_storage
- Auto-refresh before expiry
- Add to dio interceptor
- Logout on 401

### Task 1.13: Flutter - Biometric Auth (3h)

Use `local_auth` package:
- Face ID (iOS)
- Fingerprint (Android)
- Setup screen on first login
- Quick re-auth on app open

### Task 1.14: Flutter - Route Guards (2h)

`go_router` with redirects:
- Redirect to login if not authenticated
- Redirect to role-specific dashboard after login:
  - Director → `/director/dashboard`
  - HR → `/hr/dashboard`
  - Manager → `/manager/dashboard`
  - Employee → `/employee/dashboard`

---

## Acceptance Criteria

### Backend
- [ ] Login returns access + refresh tokens
- [ ] `/auth/me` returns user with permissions array
- [ ] Permission decorator blocks unauthorized
- [ ] Refresh token works
- [ ] All auth tests pass

### Frontend
- [ ] Login screen UI complete
- [ ] Successful login navigates to dashboard
- [ ] Tokens stored securely
- [ ] Biometric login works
- [ ] Auto-refresh on token expiry
- [ ] Logout clears tokens
- [ ] Role-based routing works

---

## Validation

```bash
# Backend test
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hrms.com","password":"admin123"}'

# Should return:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "bearer"
# }

# Test protected endpoint
curl http://localhost:8000/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Run all tests
pytest tests/test_auth.py -v
```

---

## Claude Code Prompt

```
Read HRMS_Architecture.md sections 2 (Roles & Permissions) and 7 (Authentication).

Implement Phase 1 (Authentication & RBAC) as described in PHASE_01_Auth.md.

Backend tasks:
1. Create User, Role, Permission, Designation models
2. Setup Alembic migrations
3. Create seed script with default roles, permissions, and users
4. Implement JWT security with access + refresh tokens
5. Build permission decorator system
6. Create auth API endpoints
7. Write comprehensive tests

Flutter tasks:
1. Create auth feature folder (Clean Architecture)
2. Implement AuthBloc with all states/events
3. Build login screen with form validation
4. Setup token storage and auto-refresh
5. Implement biometric authentication
6. Setup role-based routing with go_router

After completion:
- All endpoints tested with curl
- Login flow working end-to-end
- Biometric login functional
- All tests passing
```

---

## Next Phase

➡️ **Phase 2: Employee Management** (PHASE_02_Employee.md)
