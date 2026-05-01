# HRMS - Mobile-First HR Management System

**Stack:** FastAPI (Backend) + React (Admin Web) + Flutter (Mobile + Web) + MySQL + Redis
**Target:** IT Company with Multi-Tier Access Control
**Approach:** React for Super Admin/Admin, Flutter for everyone else (Android/iOS/Web)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Role & Permission Architecture](#2-role--permission-architecture)
3. [Database Schema](#3-database-schema)
4. [Backend (FastAPI) Structure](#4-backend-fastapi-structure)
5. [Frontend (Flutter) Structure](#5-frontend-flutter-structure)
6. [API Design](#6-api-design)
7. [Authentication & Security](#7-authentication--security)
8. [Core Modules](#8-core-modules)
9. [Mobile-First Features](#9-mobile-first-features)
10. [Deployment & DevOps](#10-deployment--devops)
11. [Phased Roadmap](#11-phased-roadmap)
12. [Daily Work Planning Module](#12-daily-work-planning-module)
13. [Justice Portal Module](#13-justice-portal-module)
14. [Field Force Management Module](#14-field-force-management-module)
15. [LMS & Examination Module](#15-lms--examination-module)
16. [Trainer Department Module](#16-trainer-department-module)
17. [Super Admin & Admin Web Portal (React)](#17-super-admin--admin-web-portal-react)
18. [Flutter Multi-Platform Setup](#18-flutter-multi-platform-setup)

---

## 1. System Overview

### Architecture Diagram

```
┌──────────────────────────┐  ┌────────────────────────────────────┐
│  React Web App           │  │  Flutter App (single codebase)      │
│  (Super Admin + Admin)   │  │  ├─ Android                         │
│  - Full system control   │  │  ├─ iOS                             │
│  - Permission management │  │  └─ Web                             │
│  - Master data setup     │  │  (Director/HR/Manager/Employee/     │
│  - Reports & analytics   │  │   Field Force/Trainer)              │
└──────────┬───────────────┘  └────────────┬───────────────────────┘
           │                                │
           │       HTTPS / JWT              │
           └────────────┬───────────────────┘
                        │
┌────────────────────▼────────────────────────────┐
│              FastAPI Backend                     │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────┐ │
│  │  Auth   │ │  RBAC   │ │ Services │ │Celery│ │
│  └─────────┘ └─────────┘ └──────────┘ └──────┘ │
└──────┬──────────────┬──────────────┬────────────┘
       │              │              │
   ┌───▼────┐   ┌─────▼────┐   ┌────▼─────┐
   │ MySQL  │   │  Redis   │   │ S3/MinIO │
   └────────┘   └──────────┘   └──────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Admin Web (React)** | | |
| Framework | React 18+ with Vite | Super Admin & Admin web app |
| Language | TypeScript | Type-safe frontend |
| State Mgmt | Zustand / Redux Toolkit | App state |
| UI Library | shadcn/ui + Tailwind | Modern UI components |
| Data Fetching | TanStack Query (React Query) | Server state |
| Routing | React Router v6 | Client-side routing |
| Forms | React Hook Form + Zod | Form validation |
| Tables | TanStack Table | Complex data tables |
| Charts | Recharts | Analytics dashboards |
| **User App (Flutter)** | | |
| Framework | Flutter 3.x | Android + iOS + Web |
| State Mgmt | flutter_bloc | Predictable state |
| Routing | go_router | Declarative routing with guards |
| DI | get_it | Dependency injection |
| HTTP | dio | API calls with interceptors |
| **Backend** | | |
| Framework | FastAPI | High-performance Python API |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| DB | MySQL 8.0+ | Primary datastore |
| Cache | Redis | Sessions, rate limiting |
| Queue | Celery + Redis | Background jobs |
| Storage | S3 / MinIO | Documents, photos |
| Auth | JWT + Refresh | Stateless authentication |
| Push | Firebase Cloud Messaging | Notifications |

---

## 2. Role & Permission Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────┐
│  TIER 1: System Administration (Web)    │
│  ├─ Super Admin (Level 6)               │
│  └─ Admin (Level 5)                     │
│  Access: React Web Only                 │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  TIER 2: Business Leadership            │
│  ├─ Director (Level 5)                  │
│  └─ HR (Level 4)                        │
│  Access: Flutter App (Web/Mobile)       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  TIER 3: Operations                     │
│  ├─ Manager (Level 3)                   │
│  ├─ Trainer (Level 2-3)                 │
│  ├─ Field Force (Level 1-2)             │
│  └─ Employee (Level 1)                  │
│  Access: Flutter App (Mobile primarily) │
└─────────────────────────────────────────┘
```

### Hybrid Model: RBAC + ABAC

- **RBAC** (Role-Based) — Super Admin, Admin, Director, HR, Manager, Employee
- **ABAC** (Attribute-Based) — Designation level, Department, Reporting hierarchy
- **Dynamic Permissions** — Super Admin can create custom roles & assign permissions

### Role Definitions

#### 🔐 Super Admin (Level 6) - SYSTEM OWNER
**Access: React Web App ONLY**

The ultimate authority. One Super Admin account per company (or 2-3 max).

- **Full system control** — Cannot be restricted by anyone
- **Create/edit/delete** any user, role, permission
- **Define Admin permissions** — Granularly control what Admin can do
- **Master data management:**
  - Companies (multi-tenant)
  - Departments, Designations
  - Leave types, Salary components
  - Holiday calendar
  - Permission catalog
- **System configuration:**
  - Email/SMS settings
  - Payment gateway
  - Storage (S3) configuration
  - Database backups
  - API keys & integrations
- **Security:**
  - View all audit logs
  - Force logout users
  - Reset passwords
  - Manage 2FA policies
- **Module management:**
  - Enable/disable modules
  - Configure module-specific settings
  - White-labeling
- **Cannot be impersonated**
- **Cannot be deleted by anyone except another Super Admin**
- **Audit log for every action**

#### ⚙️ Admin (Level 5) - DEFINED BY SUPER ADMIN
**Access: React Web App**

Admin's permissions are **completely customizable** by Super Admin. Default capabilities (configurable):

- **User Management** (if granted by Super Admin):
  - Create/edit employees
  - Reset passwords
  - Activate/deactivate users
- **Configuration** (if granted):
  - Holiday calendar
  - Department structure
  - Designations
  - Shift management
- **Reports & Analytics** (if granted):
  - All employee reports
  - Department-wise analytics
  - Compliance reports
- **Limited by Super Admin:**
  - Cannot create roles
  - Cannot grant permissions
  - Cannot access system settings
  - Cannot view financial details (unless granted)
- **Multiple Admin types possible:**
  - HR Admin
  - IT Admin
  - Finance Admin
  - Each with different permissions

#### 🎯 Director (Level 5) - BUSINESS HEAD
**Access: Flutter App (Mobile + Web)**

- Full company-wide visibility
- Approve hires above threshold (e.g., L4+)
- Approve salary above ₹X lakh CTC
- View all financial reports
- Final approval for senior resignations
- Access audit logs (read-only)
- Justice Portal recipient

#### 👥 HR (Level 4)
**Access: Flutter App (Mobile + Web)**

- Employee CRUD (create, edit, deactivate)
- Run payroll
- Manage leave/attendance policies
- Recruitment pipeline access
- Compliance reports (PF, ESI, TDS)
- Cannot view Director salary

#### 👔 Manager (Level 3, designation-based)
**Access: Flutter App (Mobile primarily)**

- View only their team's data
- Approve team leave/WFH
- Performance reviews of reportees
- Team attendance dashboard
- Cannot see other teams

#### 🎓 Trainer (Level 2-3)
**Access: Flutter App (Mobile + Web for content creation)**

- Create courses & lessons
- Manage question bank
- Conduct training sessions
- View learner progress
- Issue certificates

#### 🚗 Field Force (Level 1-2)
**Access: Flutter Mobile App ONLY**

- Daily Activity (DA) plans
- Customer visits
- Verification jobs
- GPS tracking during work
- Submit visit reports

#### 👤 Employee (Level 1)
**Access: Flutter App (Mobile primarily)**

- Own profile only
- Apply leave/WFH/reimbursement
- View own payslip
- Mark attendance (geo-fenced)
- Limited team directory view

### Designation Levels

```
L1 — Trainee, Junior Developer/Designer/QA, Field Force
L2 — Senior Developer, Sr. Designer, Junior Trainer
L3 — Tech Lead, Team Lead, Project Manager, Senior Trainer
L4 — Engineering Manager, Senior Manager, HR Manager
L5 — Director, VP, CTO, CEO, Admin, Head Trainer
L6 — Super Admin (System Owner)
```

### Platform Access Matrix

| Role | React Web | Flutter Mobile | Flutter Web |
|------|-----------|----------------|-------------|
| Super Admin | ✅ Required | ❌ | ❌ |
| Admin | ✅ Required | ❌ | ❌ |
| Director | ⚠️ Optional | ✅ | ✅ |
| HR | ⚠️ Optional | ✅ | ✅ |
| Manager | ❌ | ✅ Primary | ✅ |
| Trainer | ❌ | ✅ | ✅ Content creation |
| Field Force | ❌ | ✅ Required | ❌ |
| Employee | ❌ | ✅ Primary | ✅ |

### Permission Matrix Example

| Permission | Super Admin | Admin | Director | HR | Manager | Employee |
|------------|-------------|-------|----------|----|----|---------|----------|
| `system.config` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `role.create` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `permission.assign` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `admin.create` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `admin.permissions.set` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `module.enable` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `audit.view.all` | ✅ | ⚠️ (if granted) | ✅ | ❌ | ❌ | ❌ |
| `employee.view.all` | ✅ | ⚠️ (if granted) | ✅ | ✅ | ❌ | ❌ |
| `employee.view.team` | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| `employee.view.self` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `salary.view.all` | ✅ | ⚠️ (if granted) | ✅ | ✅ | ❌ | ❌ |
| `salary.view.team` | ✅ | ⚠️ | ✅ | ✅ | ⚠️ (range only) | ❌ |
| `salary.view.self` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `leave.approve.team` | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| `payroll.run` | ✅ | ⚠️ (if granted) | ✅ | ✅ | ❌ | ❌ |
| `asset.manage` | ✅ | ⚠️ (default yes) | ✅ | ❌ | ❌ | ❌ |

**Legend:**
- ✅ Always granted
- ⚠️ Configurable by Super Admin
- ❌ Never granted

---

## 3. Database Schema

### Core Tables

```sql
-- Users & Auth
users (id, email, phone, password_hash, is_active, mfa_enabled, created_at)
roles (id, name, level, description)
permissions (id, code, description, category)
role_permissions (role_id, permission_id)
user_roles (user_id, role_id, assigned_at)

-- Organization
companies (id, name, gst, pan, address, logo_url)
departments (id, company_id, name, head_id)
designations (id, name, level, department_id)

-- Employees
employees (
  id, user_id, employee_code, first_name, last_name,
  date_of_birth, date_of_joining, designation_id,
  department_id, reporting_to, employment_type,
  work_location, blood_group, emergency_contact,
  status, exit_date
)
employee_documents (id, employee_id, doc_type, file_url, verified)
employee_addresses (id, employee_id, type, line1, city, state, pincode)
employee_bank_details (id, employee_id, account_no, ifsc, bank_name)

-- Attendance
attendance (
  id, employee_id, date, check_in, check_out,
  check_in_lat, check_in_lng, check_in_selfie_url,
  check_out_lat, check_out_lng, status, source
)
shifts (id, name, start_time, end_time, break_duration)
employee_shifts (employee_id, shift_id, effective_from)

-- Leave
leave_types (id, name, code, days_per_year, carry_forward, encashable)
leave_balances (id, employee_id, leave_type_id, year, allocated, used, balance)
leave_requests (
  id, employee_id, leave_type_id, from_date, to_date,
  days, reason, status, approver_id, approved_at, comments
)

-- Payroll
salary_structures (id, employee_id, ctc, basic, hra, special_allowance, effective_from)
salary_components (id, name, type, calculation_type, formula)
payroll_runs (id, month, year, status, run_by, run_at, total_amount)
payslips (
  id, employee_id, payroll_run_id, gross, deductions,
  net_pay, pf, esi, tds, generated_pdf_url
)
reimbursements (
  id, employee_id, category, amount, bill_url,
  bill_date, status, approver_id, approved_at
)

-- Performance
review_cycles (id, name, start_date, end_date, status)
performance_reviews (
  id, cycle_id, employee_id, reviewer_id,
  goals_score, competency_score, overall_rating, comments
)
goals (id, employee_id, title, description, target_date, status)

-- Approvals (Universal)
approval_workflows (id, type, levels, conditions)
approvals (
  id, request_type, request_id, current_level,
  status, approver_id, approved_at, comments
)

-- Assets
assets (id, type, serial_no, brand, model, status, assigned_to)
asset_assignments (id, asset_id, employee_id, assigned_date, returned_date)

-- Audit
audit_logs (
  id, user_id, action, entity_type, entity_id,
  old_value, new_value, ip_address, user_agent, created_at
)

-- Notifications
notifications (id, user_id, title, body, type, read, created_at)
fcm_tokens (id, user_id, token, device_type, last_used)
```

### Key Relationships

- One `user` ↔ one `employee` (1:1)
- One `employee` → many `attendance` (1:N)
- One `employee` → many `leave_requests` (1:N)
- One `employee` → one `reporting_to` employee (self-referential)
- Many `roles` ↔ many `permissions` via `role_permissions`

---

## 4. Backend (FastAPI) Structure

### Folder Layout

```
hrms_backend/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Settings (Pydantic)
│   ├── database.py                # SQLAlchemy session
│   ├── dependencies.py            # Common deps (get_db, get_current_user)
│   │
│   ├── core/
│   │   ├── security.py            # JWT, password hashing
│   │   ├── permissions.py         # RBAC decorators
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── middleware.py          # Logging, CORS, audit
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── user.py
│   │   ├── employee.py
│   │   ├── attendance.py
│   │   ├── leave.py
│   │   ├── payroll.py
│   │   └── ...
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── user.py
│   │   ├── employee.py
│   │   └── ...
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── employees.py
│   │   │   ├── attendance.py
│   │   │   ├── leaves.py
│   │   │   ├── payroll.py
│   │   │   ├── approvals.py
│   │   │   ├── reports.py
│   │   │   └── admin.py
│   │   └── router.py              # Aggregates all routers
│   │
│   ├── services/                  # Business logic
│   │   ├── auth_service.py
│   │   ├── payroll_service.py
│   │   ├── leave_service.py
│   │   ├── notification_service.py
│   │   └── approval_engine.py
│   │
│   ├── tasks/                     # Celery tasks
│   │   ├── payroll_tasks.py
│   │   ├── email_tasks.py
│   │   └── report_tasks.py
│   │
│   └── utils/
│       ├── geo.py                 # Geo-fence calculations
│       ├── pdf_generator.py       # Payslip PDF
│       ├── otp.py
│       └── storage.py             # S3 uploads
│
├── alembic/                       # DB migrations
├── tests/
├── requirements.txt
├── docker-compose.yml
└── .env
```

### Key Code Patterns

**Permission Decorator:**

```python
# app/core/permissions.py
from functools import wraps
from fastapi import HTTPException, Depends

def require_permission(permission_code: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            if not current_user.has_permission(permission_code):
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_scope(scope: str):
    """scope: 'self' | 'team' | 'all'"""
    # Apply data filtering based on scope
    ...
```

**Endpoint Example:**

```python
# app/api/v1/employees.py
@router.get("/employees", response_model=List[EmployeeOut])
@require_permission("employee.view.team")
async def list_employees(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "director" or current_user.role == "hr":
        return db.query(Employee).all()
    elif current_user.role == "manager":
        return db.query(Employee).filter(
            Employee.reporting_to == current_user.employee.id
        ).all()
    else:
        return [current_user.employee]
```

**Approval Engine:**

```python
# app/services/approval_engine.py
class ApprovalEngine:
    def submit(self, request_type, request_id, employee_id):
        workflow = self.get_workflow(request_type, employee_id)
        # Auto-route to appropriate approver based on hierarchy
        ...

    def approve(self, approval_id, approver_id, comments):
        # Move to next level or mark complete
        ...
```

---

## 5. Frontend (Flutter) Structure

### Folder Layout (Feature-First)

```
hrms_mobile/
├── lib/
│   ├── main.dart
│   ├── app.dart                   # MaterialApp + MultiBlocProvider
│   │
│   ├── core/
│   │   ├── constants/
│   │   ├── theme/
│   │   │   ├── app_theme.dart
│   │   │   └── app_colors.dart
│   │   ├── network/
│   │   │   ├── dio_client.dart
│   │   │   └── interceptors.dart
│   │   ├── storage/
│   │   │   └── secure_storage.dart
│   │   ├── routing/
│   │   │   ├── app_router.dart
│   │   │   └── route_guards.dart
│   │   └── di/
│   │       └── injection.dart     # GetIt setup
│   │
│   ├── features/
│   │   ├── auth/
│   │   │   ├── data/
│   │   │   │   ├── models/
│   │   │   │   ├── datasources/
│   │   │   │   └── repositories/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   ├── repositories/
│   │   │   │   └── usecases/
│   │   │   └── presentation/
│   │   │       ├── bloc/
│   │   │       ├── pages/
│   │   │       └── widgets/
│   │   │
│   │   ├── dashboard/             # Role-specific dashboards
│   │   │   └── presentation/
│   │   │       ├── director_dashboard.dart
│   │   │       ├── hr_dashboard.dart
│   │   │       ├── manager_dashboard.dart
│   │   │       └── employee_dashboard.dart
│   │   │
│   │   ├── employee/
│   │   ├── attendance/
│   │   ├── leave/
│   │   ├── payroll/
│   │   ├── approvals/             # Universal approval inbox
│   │   ├── reimbursement/
│   │   ├── performance/
│   │   ├── documents/
│   │   ├── notifications/
│   │   └── profile/
│   │
│   ├── shared/
│   │   ├── widgets/
│   │   │   ├── permission_widget.dart
│   │   │   ├── role_based_view.dart
│   │   │   ├── app_button.dart
│   │   │   └── ...
│   │   └── extensions/
│   │
│   └── l10n/                      # Hindi + English
│
├── assets/
├── pubspec.yaml
└── ...
```

### Key Dependencies

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_bloc: ^8.1.3
  equatable: ^2.0.5
  dio: ^5.4.0
  get_it: ^7.6.4
  go_router: ^13.0.0
  flutter_secure_storage: ^9.0.0
  local_auth: ^2.1.7              # Biometric
  geolocator: ^10.1.0             # Geo-fence
  image_picker: ^1.0.4            # Selfie attendance
  firebase_messaging: ^14.7.6     # Push notifications
  cached_network_image: ^3.3.0
  intl: ^0.18.1
  fl_chart: ^0.65.0               # Charts for dashboards
  pdf: ^3.10.7                    # Payslip viewing
  permission_handler: ^11.1.0
  connectivity_plus: ^5.0.2       # Offline detection
  hive_flutter: ^1.1.0            # Local DB for offline
```

### Auth BLoC + Permission Pattern

```dart
// features/auth/presentation/bloc/auth_state.dart
class AuthAuthenticated extends AuthState {
  final User user;
  final List<String> permissions;
  final String role;
  final int designationLevel;

  bool hasPermission(String code) => permissions.contains(code);
  bool isRole(String r) => role == r;
  bool isLevelOrAbove(int level) => designationLevel >= level;
}

// shared/widgets/permission_widget.dart
class PermissionWidget extends StatelessWidget {
  final String permission;
  final Widget child;
  final Widget? fallback;

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        if (state is AuthAuthenticated && state.hasPermission(permission)) {
          return child;
        }
        return fallback ?? const SizedBox.shrink();
      },
    );
  }
}

// Usage
PermissionWidget(
  permission: 'salary.view.team',
  child: TeamSalaryCard(),
)
```

### Role-Based Routing

```dart
// core/routing/app_router.dart
final appRouter = GoRouter(
  redirect: (context, state) {
    final auth = context.read<AuthBloc>().state;
    if (auth is! AuthAuthenticated) return '/login';

    // Role-based home
    if (state.matchedLocation == '/') {
      switch (auth.role) {
        case 'director': return '/director/dashboard';
        case 'hr': return '/hr/dashboard';
        case 'manager': return '/manager/dashboard';
        default: return '/employee/dashboard';
      }
    }

    // Route guards
    if (state.matchedLocation.startsWith('/admin') &&
        !auth.hasPermission('admin.access')) {
      return '/unauthorized';
    }
    return null;
  },
  routes: [...],
);
```

---

## 6. API Design

### Base URL & Versioning

```
https://api.hrms.company.com/v1
```

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Email/phone + password → JWT |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Invalidate refresh token |
| POST | `/auth/forgot-password` | Send OTP |
| POST | `/auth/reset-password` | Verify OTP + new password |
| POST | `/auth/biometric-setup` | Register device biometric |
| GET | `/auth/me` | Current user + permissions |

### Employee Endpoints

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/employees` | `employee.view.team` (filtered) |
| GET | `/employees/{id}` | `employee.view.self/team/all` |
| POST | `/employees` | `employee.create` |
| PUT | `/employees/{id}` | `employee.edit` |
| DELETE | `/employees/{id}` | `employee.delete` |
| GET | `/employees/{id}/documents` | scoped |
| POST | `/employees/{id}/documents` | self or HR |

### Attendance Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/attendance/check-in` | Geo + selfie validation |
| POST | `/attendance/check-out` | End shift |
| GET | `/attendance/me` | Self attendance |
| GET | `/attendance/team` | Manager view |
| GET | `/attendance/report` | HR/Director |
| POST | `/attendance/regularize` | Request correction |

### Leave Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/leaves/balance` | My balance |
| POST | `/leaves/apply` | New request |
| GET | `/leaves/requests` | My requests |
| GET | `/leaves/pending-approvals` | Manager inbox |
| POST | `/leaves/{id}/approve` | Approve |
| POST | `/leaves/{id}/reject` | Reject |
| GET | `/leaves/calendar` | Team calendar |

### Payroll Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/payroll/payslips/me` | My payslips |
| GET | `/payroll/payslips/{id}/pdf` | Download PDF |
| POST | `/payroll/run` | HR triggers payroll |
| GET | `/payroll/runs` | History |
| POST | `/payroll/reimbursements` | Submit claim |
| GET | `/payroll/reimbursements/me` | My claims |

### Approval Endpoints (Universal)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/approvals/inbox` | All pending for me |
| POST | `/approvals/{id}/approve` | Approve any type |
| POST | `/approvals/{id}/reject` | Reject any type |
| GET | `/approvals/history` | My past decisions |

### Standard Response Format

```json
{
  "success": true,
  "data": { ... },
  "message": "Success",
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150
  }
}
```

### Error Format

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "You cannot view this employee's salary",
    "details": {}
  }
}
```

---

## 7. Authentication & Security

### JWT Token Strategy

- **Access Token:** 15 minutes lifetime, contains `user_id`, `role`, `permissions[]`, `designation_level`
- **Refresh Token:** 30 days, stored in secure storage on device, rotated on use
- **Device Token:** Linked to specific device (FCM), revocable per device

### Token Payload

```json
{
  "sub": "user_id",
  "emp_id": "employee_id",
  "role": "manager",
  "permissions": ["leave.approve.team", "employee.view.team"],
  "designation_level": 3,
  "department_id": 5,
  "exp": 1234567890
}
```

### Security Layers

1. **Transport:** HTTPS only, certificate pinning on mobile
2. **Auth:** JWT with short expiry + refresh
3. **MFA:** Optional TOTP for HR/Director
4. **Biometric:** Face ID / Fingerprint for app unlock
5. **Rate Limiting:** Redis-backed (e.g., 5 login attempts / 15 min)
6. **Input Validation:** Pydantic schemas (backend), form validators (mobile)
7. **SQL Injection:** SQLAlchemy ORM, no raw queries
8. **XSS/CSRF:** Not applicable (no cookies, JWT in header)
9. **Audit Log:** Every write operation logged
10. **PII Encryption:** Bank account, Aadhaar encrypted at rest
11. **Role Escalation Prevention:** Permissions verified on every request, never trust client

### Password Policy

- Min 8 characters, 1 uppercase, 1 number, 1 special
- bcrypt hashing (cost factor 12)
- Force change every 90 days for HR/Director
- Cannot reuse last 5 passwords

---

## 8. Core Modules

### 8.1 Onboarding

- Pre-joining: HR sends invite link → candidate fills form
- Document upload with OCR (Aadhaar, PAN, education)
- Auto-generate employee code
- Trigger asset assignment workflow
- Welcome email + app credentials
- First-day checklist (assigned to HR + Admin + Manager)

### 8.2 Attendance

**Modes:**
- Geo-fenced check-in (within office radius)
- Selfie + GPS for WFH
- Biometric integration (office)
- Manual regularization (with approval)

**Logic:**
```
if employee.work_mode == 'office':
    require geo_within_radius(office_location, 100m)
elif employee.work_mode == 'wfh':
    require selfie + gps_capture
elif employee.work_mode == 'hybrid':
    allow both based on day
```

### 8.3 Leave Management

**Leave Types (Indian context):**
- Casual Leave (CL) — 12/year
- Sick Leave (SL) — 12/year
- Privilege/Earned Leave (PL/EL) — 18-24/year, carry forward
- Maternity Leave — 26 weeks
- Paternity Leave — 15 days
- Bereavement Leave — 5 days
- Comp-off — earned by working holidays

**Workflow:**
1. Employee applies → balance check
2. Auto-route to direct manager
3. Manager approves/rejects (mobile push)
4. If > X days, escalate to HR/Director
5. On approval → calendar updated, balance deducted

### 8.4 Payroll

**Components:**
- Earnings: Basic, HRA, Special Allowance, Bonus, Variable Pay
- Deductions: PF (12%), ESI (0.75%), Professional Tax, TDS
- Net Pay = Gross - Deductions

**Process:**
1. Lock attendance for the month
2. HR initiates payroll run
3. Celery task computes for all employees
4. Generate payslips (PDF) → S3
5. Notify employees
6. Bank file generation (NEFT batch)
7. Compliance reports (PF/ESI/TDS challans)

### 8.5 Performance Management

- Quarterly OKR setting
- Mid-cycle check-ins (1-on-1 notes)
- Annual review (self + manager + skip-level)
- 360° feedback (peers + reportees)
- Rating calibration meeting (HR + Director)
- Increment/promotion recommendations

### 8.6 Recruitment (ATS)

- Job posting (internal + external)
- Resume parsing → candidate DB
- Interview scheduling (calendar sync)
- Feedback collection per round
- Offer letter generation (e-sign)
- Background verification

### 8.7 Asset Management

- Asset register (laptops, phones, accessories, licenses)
- Assignment workflow (Admin + Employee acknowledgment)
- Return on exit
- Maintenance tracking

### 8.8 Reports & Analytics

**Director Dashboard:**
- Headcount trend
- Attrition rate
- Cost per employee
- Department-wise productivity
- Diversity metrics

**HR Dashboard:**
- Pending approvals
- Birthdays/anniversaries
- Probation ending
- Document expiry
- Compliance status

**Manager Dashboard:**
- Team attendance %
- Pending leave approvals
- Team performance scores
- Goals completion

**Employee Dashboard:**
- Leave balance
- Next payday
- Pending tasks
- Birthday wishes feed

---

## 9. Mobile-First Features

### Must-Have UX

1. **Biometric Login** — Face ID / Fingerprint daily, password only for setup
2. **Bottom Nav (4-5 tabs)** — Home / Approvals / Attendance / Profile / More
3. **Pull-to-refresh** everywhere
4. **Skeleton loaders** instead of spinners
5. **Offline mode** — apply leave offline, sync when online
6. **Push notifications** with deep links
7. **Quick actions on home** — One-tap check-in, swipe to approve
8. **Dark mode** — System default
9. **Multi-language** — English + Hindi (more later)
10. **Gesture-based approvals** — Swipe right to approve, left to reject (Tinder-style for managers)

### Performance Targets

- App size < 30 MB
- Cold start < 2 seconds
- API response < 500ms (p95)
- Offline queue for critical actions
- Image caching aggressive

### Notifications Strategy

| Event | Channel | Recipient |
|-------|---------|-----------|
| Leave approved/rejected | Push + Email | Employee |
| Approval pending | Push | Manager |
| Payslip generated | Push + Email | Employee |
| Birthday | Push | All team |
| Document expiring | Push + Email | Employee + HR |
| Probation ending | Push | Manager + HR |

---

## 10. Deployment & DevOps

### Infrastructure

```
┌──────────────────┐
│   Cloudflare     │ (CDN + DDoS)
└────────┬─────────┘
         │
┌────────▼─────────┐
│   Nginx (LB)     │
└────────┬─────────┘
         │
┌────────▼─────────────────────┐
│  FastAPI (Gunicorn workers)  │
│  Multiple instances          │
└────────┬─────────────────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    │         │         │          │
┌───▼──┐  ┌──▼──┐  ┌───▼──┐  ┌───▼───┐
│ PG   │  │Redis│  │Celery│  │S3/MinIO│
└──────┘  └─────┘  └──────┘  └───────┘
```

### Environment Setup

- **Development:** Local Docker Compose
- **Staging:** Single VPS (Hetzner/DigitalOcean)
- **Production:** AWS / GCP / Azure with managed services

### CI/CD

- GitHub Actions for backend tests + Docker build
- Codemagic / Bitrise for Flutter builds
- Automatic staging deploy on `develop` branch
- Manual approval for production

### Monitoring

- **Logs:** Loki + Grafana / CloudWatch
- **APM:** Sentry for errors, OpenTelemetry for traces
- **Uptime:** UptimeRobot / Pingdom
- **Database:** phpMyAdmin + slow query log

### Backup Strategy

- MySQL: Daily automated backup (mysqldump), 30-day retention
- S3: Versioning enabled
- Disaster recovery RTO: 4 hours, RPO: 1 hour

---

## 11. Phased Roadmap

### Phase 1 — MVP (8 weeks)

**Goal:** Core HR operations work end-to-end

- [ ] Authentication (JWT + biometric)
- [ ] Role/permission system
- [ ] Employee CRUD with profile
- [ ] Attendance (geo + selfie)
- [ ] Leave management with approval
- [ ] Universal approval inbox
- [ ] Role-based dashboards (basic)
- [ ] Push notifications
- [ ] Profile self-service

### Phase 2 — Payroll & Compliance (6 weeks)

- [ ] Salary structure setup
- [ ] Payroll processing engine
- [ ] Payslip PDF generation
- [ ] Reimbursement workflow
- [ ] PF/ESI/TDS reports
- [ ] Form 16 generation
- [ ] Bank file export
- [ ] Tax declaration (80C, etc.)

### Phase 3 — Talent & Performance (6 weeks)

- [ ] Recruitment / ATS
- [ ] Interview management
- [ ] Offer letter + e-sign
- [ ] OKR / Goal setting
- [ ] Performance review cycles
- [ ] 360° feedback
- [ ] 1-on-1 notes

### Phase 4 — Advanced (6 weeks)

- [ ] Asset management
- [ ] Document management with expiry
- [ ] Learning & training tracking
- [ ] Internal job postings
- [ ] Employee engagement (surveys, recognition)
- [ ] Advanced analytics dashboard
- [ ] AI chatbot for HR queries

### Phase 5 — Scale (Ongoing)

- [ ] Multi-tenant (if SaaS)
- [ ] White-label options
- [ ] Mobile app for tablets
- [ ] Web admin panel
- [ ] Third-party integrations (Slack, Teams, Jira, Tally)
- [ ] AI features (resume screening, attrition prediction)

---

## Appendix A — Sample Permission Codes

```
# Employee
employee.view.self
employee.view.team
employee.view.all
employee.create
employee.edit.self
employee.edit.team
employee.edit.all
employee.delete

# Attendance
attendance.mark.self
attendance.view.self
attendance.view.team
attendance.view.all
attendance.regularize.approve

# Leave
leave.apply
leave.view.self
leave.view.team
leave.view.all
leave.approve.team
leave.approve.escalated
leave.policy.manage

# Payroll
salary.view.self
salary.view.team
salary.view.all
payroll.run
payroll.approve
reimbursement.submit
reimbursement.approve

# Admin
asset.view
asset.assign
asset.return
visitor.manage

# Reports
report.team
report.department
report.company
report.financial

# System
audit.view
settings.manage
role.manage
user.manage
```

---

## Appendix B — Sample User Stories

**As a Director:**
- I want to see company-wide attrition trends so I can plan retention strategy
- I want to approve resignations of L4+ employees with full context
- I want salary comparison with market data for my org

**As HR:**
- I want to run payroll for 200 employees in under 5 minutes
- I want pending approvals visible at a glance
- I want compliance reports auto-generated monthly

**As a Manager:**
- I want to approve leave from my phone in 2 taps
- I want to see if my team is on track with goals
- I want to give feedback right after a 1-on-1

**As an Employee:**
- I want to mark attendance with one tap
- I want to download my payslip without logging into a website
- I want to know my leave balance instantly

---

## Appendix C — Glossary

| Term | Meaning |
|------|---------|
| RBAC | Role-Based Access Control |
| ABAC | Attribute-Based Access Control |
| BLoC | Business Logic Component (Flutter pattern) |
| CTC | Cost to Company (annual salary) |
| ESS | Employee Self-Service |
| PF | Provident Fund (retirement savings) |
| ESI | Employees' State Insurance |
| TDS | Tax Deducted at Source |
| OKR | Objectives & Key Results |
| ATS | Applicant Tracking System |
| LMS | Learning Management System |

---

## 12. Daily Work Planning Module

### Concept

Employees din me **2 baar** updates submit karenge:
- **Morning (SOD)**: Pre-punchout work plan — aaj kya karenge
- **Evening (EOD)**: Work summary — aaj kya kiya

Ye replace karega WhatsApp groups ka unstructured "EOD update" culture aur har department ka kaam properly track karega.

### Daily Flow

```
9:00 AM   → Punch In (Attendance)
            ↓
9:15 AM   → Morning Plan Reminder
            ↓
            Submit Morning Plan (5 min)
            - Kya tasks plan hain
            - Priority kya hai
            - Help chahiye?
            ↓
            Manager dekhta hai team plans
            ↓
            Day's Work
            ↓
6:00 PM   → EOD Reminder
            ↓
            Submit Work Summary
            - Plan vs Actual
            - Completed tasks
            - Pending tasks
            - Blockers faced
            ↓
            Auto-link to tomorrow's plan
            ↓
6:30 PM   → Punch Out
```

### Department-Wise Templates

#### IT/Development Department

**Morning Plan:**
- Project working on (dropdown - linked to projects)
- Today's planned tasks (multiple, can link Jira tickets)
- Estimated hours per task
- Dependencies / waiting on
- Help needed from anyone?
- Meetings scheduled

**EOD Summary:**
- Tasks completed (with %)
- Tasks in progress
- Blockers faced
- Code commits count (auto-fetch if GitHub integrated)
- Hours worked (breakdown: coding/meetings/docs)
- Tomorrow's tentative plan

#### Sales Department

**Morning Plan:**
- Calls planned (count + key contacts)
- Meetings scheduled (with locations)
- Targets for the day
- Follow-ups due
- Travel plan

**EOD Summary:**
- Calls made (actual)
- Meetings held (with outcomes)
- Leads generated (new)
- Deals closed (amount)
- Pipeline updates
- Tomorrow's appointments

#### Customer Support Department

**Morning Plan:**
- Tickets in queue
- Priority cases
- Escalated cases to handle
- Training/calls scheduled

**EOD Summary:**
- Tickets handled
- Tickets resolved
- Tickets escalated
- Average response time
- Customer feedback

#### Design Department

**Morning Plan:**
- Designs to work on
- Client revisions pending
- Deliverables due

**EOD Summary:**
- Designs completed (with thumbnails)
- Revisions done
- Files delivered
- Pending work

#### Marketing Department

**Morning Plan:**
- Campaigns to manage
- Content to create
- Meetings/calls
- Vendor coordination

**EOD Summary:**
- Content created (posts, blogs)
- Campaign performance
- Engagement metrics
- Issues/learnings

#### HR/Admin Department

**Morning Plan:**
- Interviews scheduled
- Onboarding tasks
- Documentation work
- Compliance items

**EOD Summary:**
- Interviews conducted (with feedback)
- Offers rolled out
- Issues resolved
- Compliance status

#### Cleaning/Housekeeping Department

**Morning Plan (Simple Checklist):**
- Areas assigned (Reception, Floor 1, 2, 3, Washrooms, Pantry, Conference Rooms)
- Special tasks (deep clean, event prep)
- Supplies needed

**EOD Summary (Photo-Based):**
- Areas cleaned ✅
- Photos before/after (optional)
- Issues noticed (broken fixtures, leakage)
- Supplies used
- Voice note option (for low-literacy)
- Hours worked

#### Field Force / Sales Outside

**Morning Plan:**
- Visits planned (customer list)
- Route plan
- Products to demo
- Targets for visits

**EOD Summary:**
- Visits completed
- Demos given
- Outcomes
- Follow-ups scheduled
- Distance traveled

#### Production / Operations

**Morning Plan:**
- Production target
- Machine assignment
- Quality focus areas
- Material requirements

**EOD Summary:**
- Units produced
- Quality issues
- Machine downtime
- Safety incidents
- Inventory status

### Smart Features (No AI)

#### A. **Customizable Templates**
- HR/Admin can create new templates
- Add/remove/reorder fields
- Make fields mandatory/optional
- Set submission deadline (e.g., 7 PM)
- Configure reminder times
- No-code template builder

#### B. **Auto-Linking**
- Yesterday's "tomorrow plan" → Today's morning plan (pre-filled)
- Today's morning plan → Today's EOD summary (pre-filled)
- Easy edit, save time

#### C. **Multi-Format Input**
- Text typing
- Voice notes (audio file)
- Photo upload
- Checklist tap
- Hindi/English language toggle

#### D. **Quick Templates / Shortcuts**
- "Save as template" for recurring tasks
- Frequently used tasks dropdown
- Last week's updates copy option

#### E. **Tagging System**
- Tags: `#bugfix` `#feature` `#meeting` `#training` `#client-call`
- Manager filter karne me asaani

#### F. **Time Block Logging**
- Rough breakdown:
  - Coding: 5 hrs
  - Meetings: 2 hrs
  - Documentation: 1 hr
- Useful for billing, capacity planning

#### G. **Status Tags**
Update ke saath ek mood/status:
- 🟢 Going Well
- 🟡 Some Challenges
- 🔴 Need Help

#### H. **Blocker Highlighting**
- Manager ko special notification
- Red flag in team view
- Resolution time tracking

#### I. **Submission Streak**
- "15 days submitted in a row! 🔥"
- Monthly streak tracker

#### J. **Offline Mode**
- Submit offline, sync later
- Critical for field staff

#### K. **Comments Thread**
- Manager comments on update
- Employee replies
- Email avoid

#### L. **Kudos System**
- Employee mentions colleague: "Thanks @Rahul for help"
- Recorded for performance review

### Workflow Rules

#### Submission Rules
- **Mandatory** for all departments (configurable)
- **Morning**: Submit before 11 AM (configurable)
- **EOD**: Submit before 7 PM (configurable)
- Late submission → manager notified
- Missed 3+ days → HR escalation

#### Holiday/Leave Handling
- Leave pe automatic skip (no reminder)
- Half day → only relevant slot reminder
- WFH → extra fields (location ping)

#### Edit Policy
- Edit allowed within 2 hours of submission
- After that, manager approval required
- Backdated entry: 1 day allowed with reason

#### Privacy
- Direct manager: Full access
- Skip-level manager: Read access
- HR: View only on flag/issue
- Peers: No access (configurable for transparent culture)

### Manager Dashboard

#### Views

**1. Today's Summary**
```
Team Updates - Today
─────────────────────
Morning Plans: 8/10 submitted ✅
EOD Pending: 2 ⏰

Blockers Reported: 3 🔴
- Krunal: Payment gateway credentials needed
- Priya: Design approval pending from client
- Rahul: Server access issue

Top Activities:
- Coding: 45 hrs total
- Meetings: 12 hrs
- Documentation: 8 hrs
```

**2. List View** - Employee-wise daily updates
**3. Calendar View** - Date-wise heatmap
**4. Project View** - Project-wise consolidated
**5. Team Wall** - All team updates feed (with privacy)

#### Actions
- Add comments / feedback
- Like / acknowledge (👍)
- Flag for 1-on-1 discussion
- Export team report
- Bulk acknowledge

### HR/Director Dashboard

**Company-wide View:**
- Submission rate per department
- Avg hours worked
- Common blockers (manual cluster)
- Productivity trends
- Top performers
- Departments needing attention

**Reports:**
- Weekly department report
- Monthly company report
- Project-wise effort
- Client billable reports

### Database Schema

```sql
-- Templates (configurable)
dwp_templates (
  id, department_id, name, type (morning/eod),
  is_active, created_by, created_at
)

dwp_template_fields (
  id, template_id, field_name, field_type,
  is_required, options, display_order, validation_rules
)

-- Submissions
dwp_submissions (
  id, employee_id, template_id, type (morning/eod),
  date, submitted_at, status,
  total_hours, mood_rating
)

dwp_submission_data (
  id, submission_id, field_id, value, file_url
)

-- Manager interactions
dwp_comments (
  id, submission_id, commented_by,
  comment, is_kudos, requires_response, created_at
)

-- Reminders config
dwp_reminder_settings (
  id, department_id, type (morning/eod),
  reminder_times, deadline_time, escalation_enabled
)

-- Tags
dwp_tags (
  id, name, color, department_id
)

dwp_submission_tags (
  submission_id, tag_id
)
```

### API Endpoints

```
# Employee
GET  /dwp/template/morning             → Today's morning template
GET  /dwp/template/eod                 → Today's EOD template
POST /dwp/morning/submit               → Submit morning plan
POST /dwp/eod/submit                   → Submit EOD summary
GET  /dwp/me/today                     → Today's submissions
GET  /dwp/me/history                   → Past submissions
GET  /dwp/me/draft                     → Save/get draft
POST /dwp/{id}/edit                    → Edit submission

# Manager
GET  /dwp/team/today                   → Team's today updates
GET  /dwp/team/{date}                  → Specific date
GET  /dwp/team/blockers                → All blockers
POST /dwp/{id}/comment                 → Add feedback
POST /dwp/{id}/acknowledge             → Quick 👍
GET  /dwp/team/report                  → Team report

# HR/Admin
GET  /dwp/templates                    → All templates
POST /dwp/templates                    → Create new
PUT  /dwp/templates/{id}               → Update template
GET  /dwp/reports/department/{id}      → Dept analytics
GET  /dwp/reports/company              → Company-wide

# Director
GET  /dwp/dashboard                    → Executive view
GET  /dwp/insights/department          → Department insights
GET  /dwp/insights/blockers            → Common blockers report
```

### Mobile UI Flow

```
Bottom Nav: "Daily Plan" 📝

Morning Screen (9:15 AM):
┌─────────────────────────────┐
│  Good Morning, Krunal! ☀️   │
│  Mon, 30 April 2026         │
│  Submit by 11:00 AM ⏰       │
├─────────────────────────────┤
│  Project: [Trendwise ▼]      │
│                              │
│  Today's Tasks:              │
│  ┌─────────────────────┐    │
│  │ 1. Cart API endpoint│    │
│  │    ⏱ 3 hrs         │    │
│  │ 2. Coupon logic     │    │
│  │    ⏱ 2 hrs         │    │
│  │ 3. Meeting 3 PM     │    │
│  │    ⏱ 1 hr          │    │
│  │ + Add task    🎤    │    │
│  └─────────────────────┘    │
│                              │
│  Help Needed: [None ▼]       │
│  Status: 🟢 🟡 🔴            │
│                              │
│  [Save Draft] [Submit ✓]    │
└─────────────────────────────┘

EOD Screen (6:00 PM):
┌─────────────────────────────┐
│  EOD Summary                 │
│  Mon, 30 April 2026         │
├─────────────────────────────┤
│  Morning Plan vs Actual:     │
│                              │
│  ✅ Cart API endpoint (100%) │
│  🔄 Coupon logic (60%)       │
│  ✅ Meeting attended         │
│                              │
│  Blockers Faced:             │
│  🔴 Payment gateway sandbox  │
│     credentials needed       │
│                              │
│  Hours: [8.5]                │
│  Mood: 😊 😐 😔             │
│                              │
│  Tomorrow's Plan:            │
│  - Complete coupon logic     │
│  - Start checkout flow       │
│                              │
│  [Submit ✓]                 │
└─────────────────────────────┘
```

### Best Practices

✅ **Do:**
- Keep forms short (3-5 minutes max)
- Pre-fill from yesterday
- Voice notes for non-tech staff
- Photo proof for field/cleaning work
- Manager weekly review compulsory

❌ **Avoid:**
- Surveillance feel
- Punishing for honest blockers
- Too many mandatory fields
- Comparison/ranking publicly
- Linking to attendance directly

---

## 13. Justice Portal Module

### Purpose

Employee directly Director / Designated Authority ko complaint kare, **bypassing manager/HR** if needed. Critical for:
- POSH (Sexual Harassment) compliance — **legally mandatory in India**
- Workplace harassment / bullying
- Financial fraud / corruption
- Discrimination
- Policy violations
- Safety issues

### Why Bypass Hierarchy?

Sometimes manager/HR khud problem ka part hote hain. Direct route to top leadership ensures:
- No retaliation fear
- Justice for victim
- Faster resolution
- Legal compliance
- Trust in company

### Complaint Categories

#### 1. **Sexual Harassment (POSH)**
- Inappropriate comments/jokes
- Unwanted physical contact
- Stalking, repeated requests
- Showing inappropriate content
- Quid pro quo (favor exchange)
- Hostile environment

#### 2. **Workplace Harassment / Bullying**
- Verbal abuse
- Threatening behavior
- Public humiliation
- Targeted unfair treatment
- Power abuse

#### 3. **Discrimination**
- Gender, caste, religion, region
- Disability, age
- Pregnancy, marital status
- Sexual orientation

#### 4. **Financial Fraud / Corruption**
- Bribery, kickbacks
- Expense fraud
- Vendor manipulation
- Payroll fraud
- Theft

#### 5. **Policy Violations**
- Confidentiality breach
- Conflict of interest
- Moonlighting violations
- Data leaks
- Code of conduct breach

#### 6. **Safety Issues**
- Unsafe working conditions
- Health hazards
- Building safety
- Equipment safety

#### 7. **Unethical Behavior**
- Client mistreatment
- False reporting
- Plagiarism
- Resource misuse

#### 8. **General Grievance**
- Salary disputes
- Unfair treatment
- Leave denial
- Other complaints

### Privacy Levels (CRITICAL)

#### Option 1: **Anonymous** 🎭
- Identity completely hidden
- Even system encrypts
- Investigation challenging but possible
- **Use when:** Serious threat, safety concern

#### Option 2: **Confidential** 🔒
- Identity only with Director/Authority
- Manager/HR cannot see
- Most cases — best option
- Investigation can proceed

#### Option 3: **Open** 👁️
- Identity revealed
- Direct dialogue possible
- Faster resolution
- **Use when:** Comfortable, formal complaint needed

### Routing Rules

| Complaint Type | Goes To |
|----------------|---------|
| Sexual Harassment (POSH) | **ICC (Internal Complaints Committee)** — mandatory |
| Financial Fraud | Director + CFO (if Director not involved) |
| Manager-related issue | Skip-level Manager + HR Head |
| HR-related issue | Director directly |
| Director-related issue | Board Member / External Ombudsman |
| Safety Issue | Admin Head + HR + Director |
| General Grievance | HR Head |
| Discrimination | Director + HR Head |

**Critical Rule:** Complaint **NEVER** goes to accused person!

### Complaint Form

```
┌──────────────────────────────────┐
│  Submit Complaint                │
│  Your safety is our priority 🛡️ │
├──────────────────────────────────┤
│  1. Complaint Type:              │
│     [Dropdown - 8 categories]    │
│                                  │
│  2. Privacy Level:               │
│     ○ Anonymous                  │
│     ● Confidential               │
│     ○ Open (with identity)       │
│                                  │
│  3. Subject:                     │
│     [One-line summary]           │
│                                  │
│  4. Detailed Description:        │
│     [Free text + Voice 🎤]      │
│                                  │
│  5. When did it happen?          │
│     [Date + Time picker]         │
│                                  │
│  6. Where?                       │
│     [Location text]              │
│                                  │
│  7. Who is involved?             │
│     (Optional if anonymous)      │
│                                  │
│  8. Witnesses (if any):          │
│     [Names + contact]            │
│                                  │
│  9. Has this happened before?    │
│     ○ Yes ● No                   │
│     Frequency: ____              │
│                                  │
│  10. Reported earlier?           │
│      ○ Yes ● No                  │
│      To whom: ____               │
│      Response: ____              │
│                                  │
│  11. Evidence Upload:            │
│      📎 Screenshots              │
│      📷 Photos                   │
│      🎤 Audio recordings         │
│      📹 Video clips              │
│      📄 Documents                │
│      [Multiple files allowed]    │
│                                  │
│  12. What outcome you want?      │
│      ☐ Investigation             │
│      ☐ Mediation                 │
│      ☐ Disciplinary action       │
│      ☐ Just on record            │
│      ☐ Transfer                  │
│      ☐ Other: ___                │
│                                  │
│  13. Are you in immediate danger?│
│      ○ Yes ● No                  │
│      ⚠️ If Yes, emergency triggers│
│                                  │
│  [SAVE DRAFT]  [SUBMIT 🛡️]     │
└──────────────────────────────────┘
```

### Workflow

```
Employee submits complaint
    ↓
System encrypts everything
    ↓
Notification to designated authority ONLY
(Director / ICC / Ombudsman based on type)
    ↓
Authority sees complaint within 24 hrs
    ↓
Initial Assessment (1-3 days)
    ↓
Categorized by Severity:
  🔴 Critical (POSH, threat) → Action in 24 hrs
  🟠 High (Fraud, harassment) → Within 7 days
  🟡 Medium (Policy violation) → Within 15 days
  🟢 Low (Grievance) → Within 30 days
    ↓
Investigation Begins
    ↓
Evidence Collection
    ↓
Statement from accused
(without revealing complainant if confidential)
    ↓
Findings Report
    ↓
Action Taken
    ↓
Resolution & Closure
    ↓
Status update to complainant
    ↓
Feedback collection
```

### POSH Compliance (Legal Requirement)

India me **Sexual Harassment of Women at Workplace Act, 2013** ke under:

#### Mandatory Setup

**ICC (Internal Complaints Committee):**
- Min 4 members
- Presiding Officer = Senior Woman
- 50% women members
- 1 external member (NGO/lawyer)
- Term: 3 years

#### Timeline Compliance

| Stage | Timeline |
|-------|----------|
| Complaint acknowledged | 7 days |
| Investigation completed | 90 days |
| Action taken | 60 days after report |
| Annual report to govt | Mandatory |

#### Confidentiality Penalty
Identity disclosure penalty: ₹5,000 (per Act)

#### Annual Report Generation
- Number of complaints
- Cases disposed of
- Cases pending
- Action taken
- Auto-generated for District Officer

#### POSH Module Features
- Dedicated section in app
- Auto-routes to ICC only
- Standard forms as per Act
- Timeline tracker (days remaining)
- Standard investigation procedure
- Govt-format report generation
- POSH training tracker

### Security & Privacy Features

#### Data Protection

1. **End-to-end encryption** for all complaint content
2. **Separate database** (not in main HR DB)
3. **Different access keys** required (even Super Admin restricted)
4. **No screenshots allowed** in app (FLAG_SECURE on Android, similar on iOS)
5. **Watermarking** on any export (with viewer's identity)
6. **Audit log** — every view logged with timestamp + user + IP
7. **Auto-logout** after 5 minutes of inactivity
8. **Biometric required** to access justice portal
9. **Evidence files** stored in separate encrypted bucket
10. **No notification preview** on lock screen — just "New message"

#### Access Control

| Role | Access |
|------|--------|
| Director | All complaints |
| ICC Members | POSH cases only |
| HR Head | HR-related & general grievances |
| Investigators | Only assigned cases |
| IT Admin | NEVER content (only system logs) |
| DBA | Encrypted data only, can't decrypt |

#### Anti-Retaliation System

System auto-flags suspicious actions against complainant:
- Performance review suddenly drops
- Salary freeze
- Sudden transfer
- Termination initiated
- Leave rejections increase
- Negative feedback spike

→ Auto-alert to Director + ICC → Investigation

### Mobile UI Considerations

#### Sensitivity in Design

- **Calm colors** — blue/green, not aggressive red
- **Reassuring copy** — "You are safe here", "We hear you"
- **No tracking pixels** even for analytics
- **Privacy mode toggle** — hide app icon if needed
- **Disguise option** — looks like calculator/notes app (advanced)

#### Easy Access

- Quick access from main app menu
- Shake phone to open (emergency)
- Long press app icon → "Report Issue"
- Direct shortcut on home screen

#### Emotional Support

- Reassurance messages while typing
- Save draft if user closes
- "You're not alone" — statistics shown
- Helpline numbers always visible:
  - Women Helpline: 1091
  - Police: 100
  - Company Ombudsman
  - External NGO

### Sub-Modules

#### Sub-Module 1: **POSH Complaints** (Mandatory by Law)
Strict POSH Act compliance, ICC routing, separate workflow

#### Sub-Module 2: **General Grievance / Justice Portal**
All other complaints (fraud, harassment, discrimination, policy)

#### Sub-Module 3: **Voice to Leadership**
Lighter version — suggestions, internal news, feedback to Director without complaint format
- Improvement suggestions
- Internal news/updates
- Department-level issues
- Process inefficiencies
- Team morale concerns

### Database Schema (Separate DB Recommended)

```sql
-- Main complaint table
justice_complaints (
  id (UUID),
  ticket_number (visible: JC-2026-0001),
  complaint_type,
  privacy_level (anonymous/confidential/open),
  complainant_id (encrypted, null if anonymous),
  subject,
  description (encrypted),
  incident_date,
  incident_location,
  severity (critical/high/medium/low),
  status,
  submitted_at,
  assigned_to,
  resolved_at,
  resolution_summary
)

justice_evidence (
  id, complaint_id,
  file_url (encrypted bucket),
  file_type, file_size,
  uploaded_at,
  hash (tamper detection)
)

justice_accused (
  id, complaint_id,
  accused_name (encrypted),
  accused_employee_id,
  relationship_to_complainant
)

justice_witnesses (
  id, complaint_id,
  witness_name,
  witness_statement (encrypted),
  is_anonymous
)

justice_actions (
  id, complaint_id,
  action_type (notice/transfer/termination/training),
  action_date,
  taken_by,
  notes
)

justice_timeline (
  id, complaint_id,
  event_type,
  event_description,
  event_date,
  done_by
)

justice_access_log (
  id, complaint_id, user_id,
  action (viewed/edited/assigned),
  timestamp, ip_address, user_agent
)

icc_members (
  id, member_name, role,
  is_external, term_start, term_end
)

posh_annual_reports (
  id, year, total_complaints,
  resolved, pending, actions_taken,
  generated_at
)

retaliation_flags (
  id, complaint_id, employee_id,
  flag_type, detected_at, resolved
)
```

### API Endpoints

```
# Employee (Complainant)
POST /justice/submit                   → Submit complaint
GET  /justice/me                       → My complaints
GET  /justice/me/{id}                  → Complaint detail
POST /justice/me/{id}/evidence         → Add more evidence
POST /justice/me/{id}/withdraw         → Withdraw complaint
GET  /justice/resources                → Helplines, policies

# Authority (Director / ICC / Ombudsman)
GET  /justice/inbox                    → Pending complaints
GET  /justice/{id}                     → Full complaint
POST /justice/{id}/assign              → Assign investigator
POST /justice/{id}/comment             → Internal notes
POST /justice/{id}/action              → Record action
POST /justice/{id}/resolve             → Mark resolved
GET  /justice/{id}/timeline            → Full timeline
POST /justice/{id}/notify-complainant  → Update complainant

# ICC Specific (POSH)
GET  /justice/posh/cases               → POSH cases only
POST /justice/posh/{id}/investigation  → Investigation steps
GET  /justice/posh/annual-report       → Govt format report

# Reports
GET  /justice/reports/summary          → Stats only (no PII)
GET  /justice/reports/posh             → POSH compliance
```

### Sample User Stories

**As an Employee:**
- I want to report harassment without my manager knowing
- I want to upload evidence safely
- I want to track status without revealing identity
- I want emergency helpline access

**As Director:**
- I want to see all critical complaints first
- I want to assign investigators
- I want full audit trail
- I want compliance reports

**As ICC Member:**
- I want POSH cases only
- I want timeline tracker
- I want to record investigation steps
- I want govt-format report generation

---

## 14. Field Force Management Module

### Purpose

Manage employees who work **outside office** — visiting clients, doing verifications, promoting products, conducting demos. Two types:

#### Type 1: **Sales/Promotion Field Force**
Client visits, product demos, lead generation, sales closure
*Use case: Banking API products, fintech services*

#### Type 2: **Verification Field Force**
KYC verification, address verification, employment verification, document verification
*Use case: Loan applications, insurance, banking*

### Core Features (Both Types)

#### 1. **Daily Activity (DA) - Visit Plan / Beat Plan**

```
Today's Plan - Mon, 30 Apr 2026
─────────────────────────────────
1. ABC Corp - 10 AM (New Lead)
   📍 Andheri East, Mumbai
   📞 +91 98XXXXX
   
2. XYZ Ltd - 12 PM (Demo)
   📍 Bandra Kurla Complex
   📞 +91 98XXXXX
   
3. PQR Inc - 3 PM (Follow-up)
   📍 Powai
   📞 +91 98XXXXX
   
4. LMN Pvt - 5 PM (Closure)
   📍 Lower Parel

Total Distance: 45 km
Estimated Time: 8 hrs
Optimized Route: [Map View]
```

**Plan Sources:**
- Manager assigned
- Self-planned
- Auto-suggested (based on territory, last visit, priority)

#### 2. **Live GPS Tracking**

- Real-time location during work hours only
- Route history with timestamps
- Battery saver mode
- Offline tracking (sync later)
- **Privacy:** Only between check-in and check-out
- Manager dashboard with team locations on map

#### 3. **Geo-Fenced Check-In**

- Customer location pe pahunchne pe auto-detect
- Selfie + GPS capture mandatory
- Time stamp
- Address verification
- **Mock GPS detection** (block fake location apps)

#### 4. **Visit Workflow**

```
Reach Customer Location
    ↓
Auto-prompt Check-in
    ↓
Capture Selfie + GPS
    ↓
Meeting Started (timer starts)
    ↓
Fill Visit Form / Capture Details
    ↓
Upload Photos / Documents
    ↓
Customer Signature (digital)
    ↓
Check-out
    ↓
Travel to Next Location
```

#### 5. **Distance & Travel**

- Auto-calculate km traveled
- Petrol/cab reimbursement calculation
- Toll receipts upload
- Travel modes: Bike / Car / Cab / Public
- Daily total automatic

---

### SALES FIELD FORCE - Detailed Features

#### A. Lead Management

```sql
Lead Sources:
- Self-generated
- Marketing
- Referral
- Cold call
- Existing customer
- Website

Lead Status Pipeline:
New → Contacted → Qualified → Proposal Sent →
Negotiation → Won / Lost
```

#### B. Customer Database

- Company name, GST, PAN
- Contact persons (multiple)
- Industry, size, revenue
- Decision makers identified
- Buying history
- Previous interactions
- Documents uploaded
- Notes & insights

#### C. Visit Reports / Meeting Notes

**Pre-defined form for each visit:**

```
Visit Type: [Demo / Discussion / Closure / Follow-up]

Met With:
- Name: __________
- Designation: __________
- Phone: __________
- Email: __________
- Decision Maker: ☑ / ☐

Discussion Points:
- ___________________
- ___________________

Products Discussed:
☑ Banking API
☑ Payment Gateway
☐ Mobile App

Customer Interest:
🔥 Hot   ⚡ Warm   ❄️ Cold

Pain Points:
- ___________________

Competitor Mentioned:
- Razorpay / PayU / Cashfree

Budget Discussed: ₹_______

Decision Timeline:
○ Immediate ● This Month ○ Next Quarter

Next Action:
☑ Send Proposal
☑ Schedule Demo
☑ Technical Discussion

Follow-up Date: __________

Photos: [📷 Office, 📷 Meeting, 📷 Visiting Card]
Voice Note: [🎤 1:24]
Customer Signature: [✍️]
```

#### D. Product Catalog (Mobile)

- Product brochures (PDF)
- Pricing sheets
- Demo videos
- Comparison charts
- Case studies
- Customer testimonials
- **Offline access** (downloaded once)

#### E. Quote Generator

- On-the-spot quote creation
- Pre-built templates
- Discount approval workflow
- PDF generation
- Email/WhatsApp share
- Digital signature capture

#### F. Order Booking

- Order entry from field
- Inventory check
- Payment terms
- Approval workflow
- Auto-confirmation to customer
- Order tracking number

#### G. Promotional Activities Tracking

```
Today's Promotion Activity:
─────────────────────────
Location: Crowne Plaza Mumbai
Event: BFSI Summit 2026

✅ Banner placed - [Photo]
✅ 50 Brochures distributed
✅ 12 Demos given
✅ 8 Leads collected
✅ 3 Hot prospects

Photos uploaded: 8
Voice notes: 2
Visiting cards: 15 collected
```

#### H. Pipeline Management

- Visual sales funnel
- Drag-drop stage updates
- Probability percentages
- Expected revenue
- Closing date

#### I. Sales Targets & Achievement

```
Monthly Target: ₹10,00,000
Achieved: ₹6,75,000 (67.5%)
Days Remaining: 8

Pending Closures:
- ABC Corp: ₹2L (90% chance)
- XYZ Ltd: ₹1.5L (60% chance)
- PQR Inc: ₹3L (40% chance)

Forecast: ₹9,50,000 (95% target)
```

#### J. Commission Calculator

- Auto-calculate commission
- Slab-based (>10L = 5%, >20L = 8%)
- Team commission split
- Payout schedule
- Pending commission tracker

#### K. Competition Tracker

- Which competitor mentioned
- Why won/lost
- Pricing intelligence
- Product gaps identified
- Market insights

---

### VERIFICATION FIELD FORCE - Detailed Features

#### A. Verification Job Queue

```
Today's Verifications: 8

🟢 Address Verification - 4
🟡 Employment Verification - 2
🔴 Document Verification - 2

Priority:
🔥 Urgent - 2 (within 24 hrs)
⚡ Normal - 6 (within 48 hrs)
```

#### B. Job Assignment

- Manager assigns jobs
- Auto-assignment based on location
- Workload balancing
- Skip / re-assign option
- Reason for delay tracking

#### C. Verification Types

##### **Address Verification**

```
Customer: Krunal Sharma
Address: A-101, Sunrise Apt, Mumbai

Form Fields:
─────────────────
☑ Person Met:
  ○ Self ● Family ○ Neighbor
  Name: __________
  Relation: __________

☑ How long staying: __________

☑ Type of House:
  ○ Owned ● Rented ○ Family

☑ Locality Type:
  ● Posh ○ Middle ○ Slum

☑ Building visible from road?
  ● Yes ○ No

☑ Ease of reach: __________

☑ Neighbor confirmation:
  ● Yes ○ No

Documents Verified:
☑ Aadhaar Card
☑ Electricity Bill
☑ Rent Agreement

Photos Required:
📷 Building Outside
📷 Door/Nameplate
📷 Customer Selfie
📷 Documents

Geo-tag: 19.0760, 72.8777

Result:
● Positive ○ Negative ○ Doubtful

Remarks: __________

Customer Signature: [✍️]
```

##### **Employment Verification**

```
Company: Trendwise Tech
Address: BKC, Mumbai

☑ HR Met: Name __________
☑ Employee Confirmed: Yes/No
☑ Designation Verified: __________
☑ Working Since: __________
☑ Salary Range: __________
   (Verbally confirmed by HR)
☑ Employment Type:
  ● Permanent ○ Contract ○ Intern
☑ Office Premises:
  ● Genuine ○ Suspicious

Photos:
📷 Company Board
📷 Reception Area
📷 HR Person (with permission)
📷 Visiting Card

Result: Positive
```

##### **Document Verification**
- Original document check
- Photo of original
- Cross-verify with database
- Signature match
- Authenticity check

##### **Business Verification**
- Shop/office existence
- Stock visibility
- Staff count
- Customer footfall
- Monthly turnover (verbal)

#### D. Smart Forms (Configurable)

HR/Admin can:
- Create new verification type
- Add custom fields
- Mandatory vs optional
- Photo requirements
- Validation rules
- Template builder (no-code)

#### E. Photo Capture with Watermark

- Auto-watermark: date, time, location
- **Camera-only** (no gallery upload)
- Multiple angles required
- Blur detection (re-capture if blurry)
- Face detection for selfie

#### F. OCR for Documents

- Aadhaar number capture
- PAN auto-fill
- Reduces typing errors
- Faster verification

#### G. Digital Signature Capture

- Customer signs on screen
- Stored as image with timestamp
- Cannot edit later
- Legal validity

#### H. Verification Report Generation

- Auto-generate PDF report
- Standard format for clients
- All photos embedded
- Digitally signed
- Email to client + cloud storage

#### I. Quality Check / Audit

- Random 10% audit by supervisor
- Re-verification if doubt
- Quality rating per agent
- Training need identification

#### J. Fraud Detection

- Same address multiple verifications flag
- Same person photo for different cases
- GPS location mismatch alerts
- Time gap analysis
- Duplicate documents detection

#### K. TAT (Turn Around Time) Tracking

```
Job Assigned: 10:00 AM
Picked Up: 11:30 AM (1.5 hrs)
On Site: 2:00 PM (2.5 hrs)
Verification Done: 2:45 PM (45 min)
Submitted: 3:00 PM (15 min)

Total TAT: 5 hours
SLA: 24 hours ✅
```

---

### Mobile App Features (Field Force Specific)

#### 1. **Offline Mode (Critical)**
- Forms work without internet
- Photos compressed and queued
- Auto-sync when online
- Retry failed uploads

#### 2. **Battery Optimization**
- Low power mode
- GPS interval adjustable
- Smart background tracking
- Battery saver tips

#### 3. **Data Compression**
- Photo auto-compress
- Video thumbnail
- Selective sync (WiFi only for big files)
- Data usage tracker

#### 4. **Voice Commands**
- "Start verification"
- "Add note"
- "Capture photo"
- Hands-free for driving

#### 5. **Multi-language**
- Hindi, English, Marathi, Tamil, Telugu, Kannada, Bengali
- Voice input
- Forms in regional language

#### 6. **Quick Actions**
- One-tap check-in
- Emergency call button
- SOS feature
- Manager direct call
- Customer call (auto-log)

#### 7. **Map Integration**
- Optimal route suggestion
- Traffic-aware routing
- Multiple stops planning
- Estimated travel time
- Save offline maps

#### 8. **Expense Tracking on the Go**
- Petrol receipt scan
- Toll receipt
- Parking receipt
- Food bills
- Auto-categorize

---

### Manager Dashboard

#### Live Map View

- All field staff locations
- Color-coded status:
  - 🟢 On Visit
  - 🟡 Traveling
  - 🔵 At Office
  - 🔴 Idle (>2 hrs)
  - ⚫ Offline
- Click on agent for details
- Route history playback

#### Performance Dashboard

```
Today's Performance:
─────────────────────
Active Agents: 24/30

Visits Completed: 87
Visits Pending: 23
Visits Failed: 4

Total Distance: 1,245 km

Top Performers:
1. Rahul - 8 visits ✅
2. Priya - 7 visits ✅
3. Amit - 6 visits ✅

Issues:
⚠️ 3 agents idle for 2+ hours
⚠️ 2 verifications pending TAT
```

#### Productivity Metrics

- Visits per day per agent
- Conversion rate (sales)
- Verification accuracy
- TAT adherence
- Customer feedback rating
- Distance vs revenue analysis

#### Alerts & Exceptions

- Agent idle > 2 hours
- Visit time exceeding average
- Reached but not checked-in
- Out of designated area
- Suspicious pattern
- Mock location detected

#### Task Re-assignment

- Agent unavailable → reassign
- Workload balancing
- Skill-based routing
- Priority-based assignment

---

### Security & Compliance

#### A. Mock Location Detection
- Detect fake GPS apps
- Block submission if detected
- Alert manager
- Common fraud prevention

#### B. Time Manipulation
- Server time validation
- Phone time tampering detection
- Time zone consistency check

#### C. Photo Authenticity
- Camera-only (no gallery)
- EXIF data preserved
- Tamper detection
- Original timestamp

#### D. Geo-tag Verification
- Cross-check photo location
- Match with check-in location
- Alert if mismatch > 100m

#### E. Customer Privacy
- Photos encrypted at rest
- Data retention policy
- Customer consent recording
- DPDP Act compliance
- Right to deletion

#### F. Agent Security
- SOS button
- Live location share with HR
- Emergency contacts
- **Female safety protocols**
- Late hours protection
- Distress code (silent alert)

---

### Database Schema (Field Force)

```sql
-- Field employees
field_employees (
  id, employee_id, type (sales/verification),
  territory, vehicle_type, current_status,
  vehicle_number, license_number
)

-- Visit/Job assignments (Daily Activity - DA)
field_jobs (
  id, employee_id, job_type, customer_id,
  scheduled_date, scheduled_time, priority, status,
  assigned_by, assigned_at,
  completed_at, completion_status
)

-- Customer/Lead database
customers (
  id, name, type, address, geo_lat, geo_lng,
  contact_persons, industry, gst, pan,
  created_by, created_at
)

-- Visit records
visits (
  id, job_id, employee_id,
  check_in_time, check_in_lat, check_in_lng,
  check_in_selfie_url,
  check_out_time, check_out_lat, check_out_lng,
  visit_notes, outcome, signature_url,
  customer_signature_url
)

-- Visit photos
visit_photos (
  id, visit_id, photo_url, photo_type,
  geo_tagged, timestamp, watermarked,
  exif_data
)

-- GPS tracking
location_tracks (
  id, employee_id, lat, lng, accuracy,
  timestamp, battery_level, is_mock,
  speed, heading
)

-- Verification specific
verifications (
  id, job_id, type (address/employment/doc/business),
  customer_data, verification_form_data,
  result (positive/negative/doubtful),
  remarks, report_pdf_url,
  verifier_id, verified_at,
  audited_by, audit_status
)

-- Sales specific
leads (
  id, customer_id, source, status,
  expected_value, expected_close_date,
  assigned_to, score, created_at
)

opportunities (
  id, lead_id, stage, probability,
  amount, products, competitor,
  next_action, next_action_date
)

-- Targets
sales_targets (
  id, employee_id, period_type (monthly/quarterly),
  target_amount, achievement,
  period_start, period_end
)

-- Routes & Plans
visit_plans (
  id, employee_id, plan_date,
  optimized_route, total_distance,
  estimated_time, actual_time
)

-- Expenses
field_expenses (
  id, employee_id, visit_id, category,
  amount, receipt_url, status,
  approved_by, approved_at
)

-- Templates (configurable)
verification_templates (
  id, name, type, fields_json,
  photo_requirements, signature_required,
  created_by, created_at
)

-- Promotional Activities
promotion_activities (
  id, employee_id, location, event_name,
  banners_placed, brochures_distributed,
  demos_given, leads_collected,
  photos, voice_notes, date
)

-- Quotes
quotes (
  id, customer_id, employee_id,
  products, total_amount, discount,
  valid_until, status, pdf_url
)
```

### API Endpoints

```
# Field Employee
GET  /field/jobs/today                 → Today's assignments (DA)
GET  /field/jobs/{id}                  → Job details
POST /field/jobs/{id}/checkin          → Check-in at location
POST /field/jobs/{id}/checkout         → Check-out
POST /field/jobs/{id}/visit-form       → Submit visit form
POST /field/jobs/{id}/photos           → Upload photos
POST /field/jobs/{id}/signature        → Customer signature
POST /field/location/track             → Periodic location update
GET  /field/route/optimize             → Get optimized route

# Sales Specific
GET  /field/leads                      → My leads
POST /field/leads                      → New lead
POST /field/quotes                     → Create quote
POST /field/orders                     → Book order
GET  /field/targets/me                 → My targets
GET  /field/products                   → Product catalog
POST /field/promotions                 → Log promo activity

# Verification Specific
GET  /field/verifications/queue        → Pending verifications
POST /field/verifications/{id}/submit  → Submit verification
POST /field/verifications/{id}/photos  → Verification photos
GET  /field/templates/{type}           → Get template
POST /field/ocr/aadhaar                → OCR Aadhaar
POST /field/ocr/pan                    → OCR PAN

# Manager
GET  /field/team/live-map              → Live team locations
GET  /field/team/performance           → Team metrics
POST /field/jobs/assign                → Assign jobs
POST /field/jobs/reassign              → Reassign
GET  /field/team/alerts                → Exceptions
GET  /field/audit/random               → Random audits

# Admin
POST /field/templates                  → Create template
POST /field/territories                → Define territories
GET  /field/reports/tat                → TAT reports
GET  /field/reports/fraud              → Fraud detection
```

### Mobile UI Flow

#### Home Screen (Field Employee)

```
┌──────────────────────────────┐
│  Hi Krunal! 👋               │
│  Today: Mon, 30 Apr          │
├──────────────────────────────┤
│  📍 Today's Plan: 8 visits   │
│  ✅ Completed: 3             │
│  🔄 In Progress: 1           │
│  📋 Pending: 4               │
├──────────────────────────────┤
│  [START NEXT VISIT]          │
├──────────────────────────────┤
│  Quick Actions:              │
│  📷 Add Visit                │
│  💰 Add Expense              │
│  🗺️ View Route              │
│  📞 Contact Manager          │
├──────────────────────────────┤
│  Today's Stats:              │
│  Distance: 23 km             │
│  Hours: 5.5                  │
│  Demos: 2                    │
│  Leads: 5                    │
└──────────────────────────────┘
```

#### Visit Detail Screen

```
┌──────────────────────────────┐
│  Visit #4521                 │
│  ABC Corp - Demo             │
├──────────────────────────────┤
│  📍 BKC, Mumbai              │
│  🕐 12:00 PM                 │
│  👤 Mr. Sharma (CEO)         │
│  📞 +91 98XXXXX              │
├──────────────────────────────┤
│  [📞 Call] [📧 Email]        │
│  [🗺️ Navigate]              │
├──────────────────────────────┤
│  ✓ Check-in (auto when near) │
│                              │
│  After meeting:              │
│  ☐ Fill visit form           │
│  ☐ Upload photos             │
│  ☐ Get signature             │
│  ☐ Check-out                 │
└──────────────────────────────┘
```

### Phased Rollout (Field Force)

#### Phase 1: Basic Field Force (4 weeks)
- Visit planning (DA)
- Check-in/check-out with GPS + selfie
- Basic visit form
- Photo upload
- Manager dashboard with live map

#### Phase 2: Sales Module (4 weeks)
- Lead management
- Customer database
- Detailed visit reports
- Quote generation
- Pipeline management
- Promotional activity tracking

#### Phase 3: Verification Module (4 weeks)
- Job queue management
- Configurable verification templates
- OCR for documents
- Report generation
- TAT tracking
- Fraud detection

#### Phase 4: Advanced Features (4 weeks)
- Route optimization
- Robust offline mode
- Advanced analytics
- API for client integration
- Multi-language support

#### Phase 5: Polish & Scale
- Performance tuning
- Battery optimization
- Voice features
- Advanced fraud detection

### Use Cases for Your Stack

Aapke fintech/banking integration background ke hisab se:

**1. Banking KYC Field Force**
- Loan application address verification
- Small business loan customer visit
- Credit card verification
- Account opening documentation

**2. Fintech Sales Field Force**
- Banking API product demos
- Payment gateway sales (JioPay, NeoPayment style)
- BBPS integration sales
- Merchant onboarding

Ye module aapke existing `nakshtralogy/flutter_user` app me ek new module ke roop me add ho sakta hai, with shared auth and HR core.

---

## 15. LMS & Examination Module

### Purpose

**Learning Management System** with **MCQ-based examinations** for every employee, organized **department-wise**. Goals:

- Skill development & upskilling
- Compliance training (POSH, Safety, Code of Conduct)
- Onboarding training for new joiners
- Department-specific knowledge tests
- Certification programs
- Performance improvement
- Promotion criteria

### Why Department-Wise?

Har department ki learning needs alag hain:
- **IT**: Coding, frameworks, cloud, security
- **Sales**: Pitching, negotiation, product knowledge
- **HR**: Labor laws, POSH, recruitment
- **Field Force**: Verification process, safety, customer handling
- **Cleaning**: Hygiene, safety, equipment usage
- **Customer Support**: Communication, product, escalation

### Module Architecture

```
┌──────────────────────────────────────────┐
│            COURSE LIBRARY                │
│  (Created by Trainer Dept)               │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│        LEARNING PATHS                    │
│  (Department-wise / Role-wise            │
│   curated sequences)                     │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         COURSE CONSUMPTION               │
│  (Videos, PDFs, articles, quizzes)       │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         EXAMINATION                      │
│  (MCQ tests, time-bound,                 │
│   pass/fail criteria)                    │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         CERTIFICATION                    │
│  (Auto-generated certificates,           │
│   shareable, expirable)                  │
└──────────────────────────────────────────┘
```

---

### LMS Features

#### A. Course Categories

```
🎯 Mandatory (Compliance):
- POSH Awareness
- Code of Conduct
- Information Security
- Anti-Bribery
- Data Privacy (DPDP Act)
- Workplace Safety
- Fire Safety

📚 Department Courses:
- IT/Development
- Sales & Marketing
- HR & Admin
- Field Force
- Customer Support
- Operations
- Cleaning/Housekeeping

🎓 Skill Development:
- Communication Skills
- Leadership
- Time Management
- MS Office / Tools
- Language (English, Regional)

🌟 Career Growth:
- L1 to L2 Promotion Course
- Manager Readiness
- Advanced Specialization

📋 Onboarding:
- Company Overview
- Policies & Procedures
- Tools & Systems
- Buddy Program
```

#### B. Course Structure

```
Course: "Banking API Integration Basics"
├── Module 1: Introduction
│   ├── Video Lesson (10 min)
│   ├── PDF Reading (15 min)
│   └── Quiz (5 MCQs)
├── Module 2: Authentication
│   ├── Video Lesson (15 min)
│   ├── Code Examples
│   └── Quiz (10 MCQs)
├── Module 3: API Endpoints
│   ├── Video Lesson (20 min)
│   ├── Hands-on Exercise
│   └── Quiz (15 MCQs)
├── Module 4: Error Handling
│   ├── Video Lesson (10 min)
│   └── Quiz (5 MCQs)
└── Final Examination
    ├── 50 MCQs
    ├── Time: 60 minutes
    ├── Passing: 70%
    └── Certificate on pass
```

#### C. Content Types

- **Video Lessons** — Trainer recorded / external (YouTube embed)
- **PDF Documents** — Reference material
- **Articles** — Long-form text content
- **Slide Presentations** — PPT/PDF
- **Audio Lessons** — Podcasts
- **Interactive Exercises** — Code playgrounds, simulations
- **External Links** — Curated resources
- **Live Sessions** — Webinars (via Zoom/Meet integration)
- **Quizzes** — Knowledge checks
- **Assignments** — Project-based learning

#### D. Learning Paths

**Pre-defined sequences for departments/roles:**

```
Path: "Junior Developer → Senior Developer"
├── Step 1: Advanced Git (Course)
├── Step 2: System Design Basics (Course)
├── Step 3: Code Review Skills (Course)
├── Step 4: Mentorship Skills (Course)
├── Step 5: Final Assessment (Exam)
└── Completion: Promotion eligible

Path: "New Field Force Onboarding"
├── Step 1: Company Overview
├── Step 2: Field Force App Tutorial
├── Step 3: Customer Etiquette
├── Step 4: Verification Process
├── Step 5: Safety Protocols
├── Step 6: Mock Verification
└── Final Exam → Field Ready Certificate
```

#### E. Mandatory vs Optional

- **Mandatory courses** — Must complete with deadline
  - POSH (Annual)
  - Information Security (Annual)
  - Department-specific compliance
- **Optional courses** — Self-development
- **Recommended** — Manager assigned

#### F. Course Assignment

**Auto-Assignment Rules:**
- New joiner → Onboarding path
- Department change → New department path
- Promotion → Leadership path
- Annual → Compliance refresh
- Probation → Probation path

**Manual Assignment:**
- Manager assigns to team
- HR assigns company-wide
- Self-enroll (optional courses)

#### G. Progress Tracking

```
Course: "Banking API Integration"
─────────────────────────────────
Progress: 65% ████████░░

Modules:
✅ Module 1: Introduction (100%)
✅ Module 2: Authentication (100%)
🔄 Module 3: API Endpoints (40%)
⏳ Module 4: Error Handling (0%)
⏳ Final Exam (Locked)

Time Spent: 2h 15min
Average Score: 85%
Estimated Completion: 1h 30min remaining
```

#### H. Reminders & Notifications

- Course assigned notification
- Daily/weekly study reminders
- Deadline approaching alerts
- New course recommendations
- Certificate expiry warnings
- Exam scheduled reminders

#### I. Gamification (Optional)

- **Points** — Per lesson, quiz, course completion
- **Badges** — "Quick Learner", "Perfect Scorer", "Streak Master"
- **Leaderboard** — Department-wise (optional)
- **Streaks** — "10 days learning streak 🔥"
- **Levels** — Bronze → Silver → Gold → Platinum learner

#### J. Mobile-First Features

- **Offline mode** — Download videos, read offline
- **Resume from where left** — Multi-device sync
- **Voice note answers** — For low-literacy users
- **Hindi/English** — Multi-language support
- **Watch speed control** — 0.5x to 2x
- **Subtitles** — Multi-language
- **Bookmark** lessons
- **Take notes** while watching

---

### Examination System (MCQ-Based)

#### A. Question Types

**Primary: Multiple Choice Questions (MCQ)**
- Single correct answer
- Multiple correct answers
- True/False
- Fill in the blank (optional dropdown)
- Match the following
- Sequence ordering

#### B. Question Bank

**Organization:**
```
Question Bank
├── By Department
│   ├── IT
│   ├── Sales
│   ├── HR
│   └── Field Force
├── By Topic
│   ├── Banking APIs
│   ├── Communication
│   ├── POSH
│   └── Safety
├── By Difficulty
│   ├── Easy
│   ├── Medium
│   └── Hard
└── By Language
    ├── English
    ├── Hindi
    └── Regional
```

#### C. Question Format

```
Question ID: Q-IT-001
Department: IT/Development
Topic: Banking APIs
Difficulty: Medium
Language: English
Marks: 2

Question:
What does HMAC-SHA256 stand for in 
API authentication?

Options:
○ A. Hash Message Auth Code - SHA256
● B. Hash-based Message Authentication 
     Code with SHA-256
○ C. Hyper Message Auth Code SHA256
○ D. Hash Method Auth Cipher SHA256

Explanation (shown after submission):
HMAC-SHA256 combines a cryptographic hash 
function (SHA-256) with a secret key for 
message authentication...

Time to answer: 60 seconds
```

#### D. Exam Configuration

**Trainer/HR can set:**

```
Exam Setup:
─────────────────────
Title: Banking API Final Exam
Department: IT
Course Linked: Banking API Integration
Total Questions: 50
Time Limit: 60 minutes
Passing Score: 70%

Question Selection:
○ Fixed (same questions for all)
● Random (from question pool)
   - Easy: 20 questions
   - Medium: 20 questions
   - Hard: 10 questions

Settings:
☑ Shuffle questions
☑ Shuffle options
☑ Show timer
☑ Show progress bar
☐ Allow review before submit
☐ Allow back navigation
☑ Auto-submit on time end
☐ Show explanation after each Q
☑ Show explanation at end
☑ Negative marking: -0.5

Anti-Cheating:
☑ Full-screen mode
☑ Disable copy-paste
☑ Webcam proctoring (optional)
☑ Tab switch detection
☑ Multiple device check
☑ Random question order

Attempts Allowed: 3
Cool-down between attempts: 24 hours
```

#### E. Exam Modes

**1. Practice Mode**
- Unlimited attempts
- See correct answers immediately
- No score record
- For learning

**2. Self-Assessment Mode**
- Limited attempts
- Score recorded
- For self-evaluation
- No certificate

**3. Certification Mode**
- Strict timing
- Limited attempts
- Score recorded
- Certificate on pass
- Anti-cheating enabled

**4. Mandatory Compliance Mode**
- Must pass
- Repeat until pass
- Auto-reminder
- Compliance report generated

#### F. Exam Flow

```
Start Exam
    ↓
Identity Verification
(Selfie + Password)
    ↓
Read Instructions
    ↓
Click "Start Exam"
    ↓
Full-screen mode activated
    ↓
Timer starts
    ↓
Answer Questions (one by one or all)
    ↓
[Auto-save every 30 seconds]
    ↓
Click "Submit" OR Time runs out
    ↓
Review Confirmation
    ↓
Final Submit
    ↓
Auto-evaluation (instant)
    ↓
Result Display:
- Score: X/Y
- Percentage
- Pass/Fail
- Time taken
- Question-wise analysis
- Wrong answers with explanations
    ↓
If Pass: Certificate Generated
If Fail: Retake option after cool-down
```

#### G. Anti-Cheating Measures

**Technical:**
- Full-screen lock (exit = warning)
- Tab switch detection (3 warnings = auto-submit)
- Copy-paste disabled
- Right-click disabled
- Screenshot blocked (Android FLAG_SECURE)
- Multiple device login detection
- IP address logging
- Browser fingerprint
- Webcam monitoring (optional, with consent)
- Question randomization
- Option shuffling

**Behavioral:**
- Time per question tracking (too fast = flag)
- Suspicious pattern detection
- Statistical anomaly alerts
- Re-take if cheating detected

#### H. Result & Analytics

**For Employee:**
```
Exam Result
─────────────────────
Course: Banking API Integration
Date: 30 April 2026
Time: 45 minutes (out of 60)

Score: 38/50 (76%)
Status: ✅ PASSED

Section-wise Performance:
Authentication: 9/10 (90%) 🟢
API Endpoints: 16/20 (80%) 🟢
Error Handling: 8/15 (53%) 🟡
Best Practices: 5/5 (100%) 🟢

Strengths:
- Authentication concepts
- Best practices

Improvement Areas:
- Error handling patterns
- Edge cases

[View Wrong Answers]
[Download Certificate]
[Retake Practice Test]
```

**For Manager:**
- Team performance dashboard
- Individual scores
- Department average
- Topic-wise weakness
- Training need identification

**For HR/Director:**
- Company-wide compliance status
- Department comparison
- Pass/fail trends
- Certification status
- Training ROI

#### I. Certification

**Auto-generated certificates:**
- PDF format
- Unique certificate number
- QR code for verification
- Shareable on LinkedIn
- Expiry date (if applicable)
- Re-certification reminders
- Digital signature
- Tamper-proof

**Sample Certificate:**
```
╔═══════════════════════════════════════╗
║                                       ║
║         CERTIFICATE OF                ║
║         COMPLETION                    ║
║                                       ║
║   This is to certify that             ║
║                                       ║
║         Krunal Sharma                 ║
║                                       ║
║   has successfully completed          ║
║                                       ║
║    Banking API Integration            ║
║                                       ║
║   Score: 76%                          ║
║   Date: 30 April 2026                 ║
║   Cert ID: NSK-2026-001234            ║
║                                       ║
║   [QR Code]                           ║
║                                       ║
║   Valid Until: 30 April 2028          ║
║                                       ║
║   _______________                     ║
║   Director Signature                  ║
╚═══════════════════════════════════════╝
```

#### J. Department-Wise Examination Examples

**IT/Development:**
- Coding fundamentals
- Framework-specific (Flutter, FastAPI, React)
- Database concepts
- Cloud (AWS, GCP, Azure)
- DevOps & CI/CD
- Security best practices
- Banking APIs (your domain)

**Sales:**
- Product knowledge test
- Sales process
- CRM usage
- Negotiation scenarios
- Customer objection handling
- Pricing knowledge

**HR:**
- Labor laws
- POSH Act
- Recruitment process
- Payroll fundamentals
- Performance management

**Field Force:**
- Verification procedures
- Customer interaction protocols
- Safety regulations
- Documentation accuracy
- App usage proficiency
- Ethical conduct

**Cleaning/Housekeeping:**
- Hygiene standards
- Equipment usage
- Chemical handling safety
- Emergency procedures
- Customer interaction

**Customer Support:**
- Product knowledge
- Communication skills
- Escalation matrix
- CRM/ticketing tool
- Conflict resolution

---

### Database Schema (LMS & Exams)

```sql
-- Courses
courses (
  id, title, description, category,
  department_id, difficulty_level,
  estimated_hours, thumbnail_url,
  status (draft/published/archived),
  is_mandatory, validity_months,
  created_by, created_at
)

course_modules (
  id, course_id, title, description,
  order, estimated_minutes
)

course_lessons (
  id, module_id, title, content_type,
  (video/pdf/article/audio/external_link),
  content_url, duration_minutes,
  order, is_mandatory
)

-- Learning Paths
learning_paths (
  id, name, description, target_role,
  target_department, total_courses,
  estimated_days
)

learning_path_courses (
  path_id, course_id, sequence_order,
  is_mandatory
)

-- Enrollments
course_enrollments (
  id, employee_id, course_id,
  enrolled_at, enrolled_by, due_date,
  status (assigned/in_progress/completed),
  progress_percentage,
  completed_at, last_accessed_at
)

lesson_progress (
  id, enrollment_id, lesson_id,
  status, time_spent, completed_at,
  notes, bookmarked
)

-- Question Bank
question_bank (
  id, question_text, question_type
  (single_choice/multi_choice/true_false/match),
  department_id, topic, difficulty,
  language, marks, time_seconds,
  explanation, created_by, status
)

question_options (
  id, question_id, option_text,
  is_correct, order
)

-- Exams
exams (
  id, title, description, course_id,
  department_id, total_questions,
  time_limit_minutes, passing_percentage,
  exam_type (practice/assessment/certification/mandatory),
  question_selection (fixed/random),
  shuffle_questions, shuffle_options,
  allow_review, attempts_allowed,
  cooldown_hours, negative_marking,
  anti_cheat_settings,
  validity_months,
  status, created_by
)

exam_questions (
  exam_id, question_id, marks_override
)

-- Exam Attempts
exam_attempts (
  id, exam_id, employee_id,
  started_at, submitted_at,
  time_taken_seconds,
  total_score, percentage,
  status (in_progress/submitted/auto_submitted/abandoned),
  passed, attempt_number,
  ip_address, device_info,
  cheating_flags
)

attempt_answers (
  id, attempt_id, question_id,
  selected_option_ids, answer_text,
  is_correct, marks_awarded,
  time_taken_seconds
)

-- Certificates
certificates (
  id, employee_id, course_id, exam_attempt_id,
  certificate_number, issued_date,
  expiry_date, pdf_url, qr_code,
  is_valid, revoked_reason
)

-- Analytics
exam_analytics (
  id, exam_id, date,
  total_attempts, total_passed, total_failed,
  average_score, average_time
)

-- Reminders
lms_reminders (
  id, employee_id, course_id, exam_id,
  reminder_type, scheduled_at, sent_at
)

-- Compliance Tracking
compliance_requirements (
  id, course_id, frequency_months,
  applicable_to_role, applicable_to_dept
)

compliance_status (
  id, employee_id, requirement_id,
  last_completed_at, next_due_at,
  status (compliant/due/overdue)
)
```

### API Endpoints (LMS & Exams)

```
# Employee - Courses
GET  /lms/courses                      → Browse all courses
GET  /lms/courses/recommended          → For me
GET  /lms/courses/mandatory            → Must complete
GET  /lms/courses/{id}                 → Course detail
POST /lms/courses/{id}/enroll          → Self-enroll
GET  /lms/my-courses                   → Enrolled courses
GET  /lms/my-courses/in-progress       → Currently learning

# Employee - Lessons
GET  /lms/lessons/{id}                 → Lesson content
POST /lms/lessons/{id}/start           → Mark started
POST /lms/lessons/{id}/complete        → Mark complete
POST /lms/lessons/{id}/notes           → Save notes
POST /lms/lessons/{id}/bookmark        → Bookmark

# Employee - Exams
GET  /lms/exams/upcoming               → Upcoming exams
GET  /lms/exams/{id}/start             → Start exam
POST /lms/exams/{id}/answer            → Save answer (auto)
POST /lms/exams/{id}/submit            → Final submit
GET  /lms/exams/{id}/result            → My result
GET  /lms/my-attempts                  → All attempts
GET  /lms/my-attempts/{id}/review      → Review attempt

# Employee - Certificates
GET  /lms/certificates/me              → My certificates
GET  /lms/certificates/{id}/download   → Download PDF
GET  /lms/certificates/verify/{number} → Verify (public)

# Trainer - Course Management
POST /lms/courses                      → Create course
PUT  /lms/courses/{id}                 → Update
POST /lms/courses/{id}/publish         → Publish
POST /lms/courses/{id}/modules         → Add module
POST /lms/modules/{id}/lessons         → Add lesson
POST /lms/lessons/upload               → Upload content

# Trainer - Question Bank
GET  /lms/questions                    → Browse questions
POST /lms/questions                    → Create question
PUT  /lms/questions/{id}               → Update
POST /lms/questions/import             → Bulk import (CSV)
GET  /lms/questions/by-topic/{topic}   → By topic

# Trainer - Exam Management
POST /lms/exams                        → Create exam
PUT  /lms/exams/{id}                   → Update settings
POST /lms/exams/{id}/questions         → Add questions
GET  /lms/exams/{id}/analytics         → Performance data

# Manager
GET  /lms/team/progress                → Team learning
POST /lms/team/assign-course           → Assign to team
GET  /lms/team/exam-results            → Team scores
GET  /lms/team/compliance              → Compliance status

# HR/Admin
GET  /lms/compliance/dashboard         → Company-wide
POST /lms/courses/assign-bulk          → Bulk assign
GET  /lms/reports/training             → Training reports
GET  /lms/reports/certifications       → Cert reports

# Director
GET  /lms/dashboard/executive          → Executive view
GET  /lms/insights/department          → Dept analytics
GET  /lms/insights/training-roi        → ROI analysis
```

### Mobile UI Flow

#### Course List Screen

```
┌──────────────────────────────┐
│  My Learning 📚              │
├──────────────────────────────┤
│  📌 Mandatory (2)            │
│  ┌─────────────────────┐    │
│  │ POSH Annual 2026    │    │
│  │ Due: 15 May        🔴│    │
│  │ ████░░░░░░ 40%      │    │
│  └─────────────────────┘    │
│                              │
│  🔄 In Progress (3)          │
│  ┌─────────────────────┐    │
│  │ Banking API         │    │
│  │ ██████░░░░ 65%      │    │
│  └─────────────────────┘    │
│                              │
│  💡 Recommended (5)          │
│  Browse all →                │
└──────────────────────────────┘
```

#### Lesson Screen

```
┌──────────────────────────────┐
│  ← Banking API > Module 3    │
│  Lesson 2: Auth Tokens       │
├──────────────────────────────┤
│  ▶ [Video Player]            │
│   12:34 / 18:45              │
│   ⚙️ Speed: 1.25x            │
├──────────────────────────────┤
│  📝 Notes  🔖 Bookmark       │
├──────────────────────────────┤
│  Description:                │
│  Learn about JWT tokens...   │
│                              │
│  [Mark Complete ✓]           │
└──────────────────────────────┘
```

#### Exam Screen

```
┌──────────────────────────────┐
│  Banking API Final Exam      │
│  ⏱ 45:23 remaining           │
│  Question 12 of 50           │
├──────────────────────────────┤
│  Q: What is HMAC-SHA256?     │
│                              │
│  ○ A. Hash Message Auth      │
│      Code - SHA256           │
│                              │
│  ● B. Hash-based Message     │
│      Authentication Code     │
│      with SHA-256            │
│                              │
│  ○ C. Hyper Message Auth     │
│                              │
│  ○ D. Hash Method Auth       │
├──────────────────────────────┤
│  [← Previous] [Next →]       │
│                              │
│  Progress: ████████░░ 24%    │
│                              │
│  [🏁 Submit Exam]            │
└──────────────────────────────┘
```

#### Result Screen

```
┌──────────────────────────────┐
│  🎉 Congratulations!         │
│                              │
│      ✅ PASSED               │
│                              │
│      Score: 76%              │
│      38 / 50                 │
├──────────────────────────────┤
│  Performance:                │
│  Auth: 90% 🟢               │
│  Endpoints: 80% 🟢           │
│  Errors: 53% 🟡             │
├──────────────────────────────┤
│  [📜 Download Certificate]   │
│  [📝 Review Wrong Answers]   │
│  [📊 Detailed Analysis]      │
└──────────────────────────────┘
```

---

## 16. Trainer Department Module

### Purpose

Dedicated module for **Trainer Department** team members who:
- Create training content
- Conduct training sessions (online + offline)
- Manage question banks
- Design exams
- Track learner progress
- Generate training reports
- Mentor employees

### Trainer Roles & Hierarchy

```
Head Trainer / L&D Head (L4-L5)
    ├── Senior Trainers (L3)
    │   ├── Subject Matter Experts (SMEs)
    │   ├── Department-specific trainers
    │   └── Soft Skills Trainers
    │
    ├── Junior Trainers (L2)
    │   ├── Onboarding trainers
    │   └── Compliance trainers
    │
    └── External Trainers (Contract)
        ├── Industry experts
        └── Specialized skills
```

### Trainer Permissions

| Permission | Head Trainer | Senior | Junior | External |
|------------|--------------|--------|--------|----------|
| Create courses | ✅ | ✅ | ⚠️ (with approval) | ⚠️ (assigned only) |
| Edit any course | ✅ | ⚠️ (own dept) | ❌ | ❌ |
| Publish courses | ✅ | ✅ | ❌ | ❌ |
| Create exams | ✅ | ✅ | ⚠️ | ⚠️ |
| Question bank full | ✅ | ✅ | ⚠️ (own topic) | ⚠️ (assigned) |
| View all results | ✅ | ✅ (own dept) | ⚠️ | ❌ |
| Conduct sessions | ✅ | ✅ | ✅ | ✅ |
| Approve courses | ✅ | ❌ | ❌ | ❌ |
| Trainer assignment | ✅ | ❌ | ❌ | ❌ |

---

### Core Trainer Features

#### A. Content Creation Studio

**Course Builder (Drag-Drop):**
```
┌──────────────────────────────────────┐
│  Course Builder                      │
├──────────────────────────────────────┤
│  Course: Banking API Integration     │
│                                      │
│  📑 Module 1: Introduction         ↕ │
│    ├── 📹 Video Lesson 1          ↕ │
│    ├── 📄 PDF Reading             ↕ │
│    └── ❓ Quiz (5 Q)              ↕ │
│                                      │
│  📑 Module 2: Authentication       ↕ │
│    ├── 📹 Video Lesson 2          ↕ │
│    ├── 💻 Code Example            ↕ │
│    └── ❓ Quiz (10 Q)             ↕ │
│                                      │
│  [+ Add Module]                      │
│  [+ Add Lesson]                      │
│                                      │
│  [Save Draft] [Publish]              │
└──────────────────────────────────────┘
```

#### B. Video Recording / Upload

**Options:**
- Direct upload (MP4, MOV)
- Screen recording (web)
- Record video in-app (mobile)
- YouTube/Vimeo embed
- Auto-transcription (without AI - manual subtitle option)
- Multi-language audio tracks
- Compression on upload

#### C. Question Creation Tools

**Bulk Question Import:**
- CSV/Excel upload template
- Bulk MCQ creation
- Image embedding in questions
- Mathematical formulas (LaTeX)
- Code snippets in questions
- Audio/video questions

**Question Template:**
```
Question Bank Manager
─────────────────────
Topic: Banking APIs
Sub-topic: Authentication
Difficulty: Medium
Language: English

Question:
[Rich text editor with image/code support]

Options:
A. [Option text]
B. [Option text] ✓ Correct
C. [Option text]
D. [Option text]

Explanation:
[Detailed explanation shown after attempt]

Tags: #banking #api #auth
Time Limit: 60 sec
Marks: 2

[Save] [Save & Add Another]
```

#### D. Live Training Sessions

**Schedule & Conduct:**
- Schedule training (calendar integration)
- Online: Zoom/Meet/Teams integration
- Offline: Conference room booking
- Hybrid sessions
- Recurring sessions
- Mandatory vs optional
- Capacity limits

**Session Management:**
- Send invites to participants
- Pre-session reading material
- Live attendance marking (QR code scan)
- Live polls during session
- Q&A management
- Recording for absentees
- Post-session quiz
- Feedback collection

#### E. Trainer Dashboard

```
Trainer Dashboard
──────────────────────────
👨‍🏫 Welcome, Senior Trainer!

📊 My Courses:
- Active: 12
- Drafts: 3
- Total Learners: 245

📅 Upcoming Sessions:
- Today: 2 sessions
- This Week: 8 sessions

📋 Pending Tasks:
- Review 3 questions
- Update 1 course
- Grade 5 assignments

📈 Stats (This Month):
- New courses: 2
- Sessions conducted: 24
- Hours of training: 48
- Avg learner rating: 4.5/5
- Pass rate: 82%

🎯 Top Performing Course:
"Banking API Integration"
- 156 enrolled
- 89% completion
- 4.7/5 rating
```

#### F. Learner Progress Tracking

**Per Course:**
```
Course: Banking API Integration
─────────────────────────────────
Total Enrolled: 156
Active: 120
Completed: 36
Dropped: 0

Average Progress: 65%
Average Time: 8.5 hours

Performance:
- Pass Rate: 89%
- Avg Score: 78%
- Best Score: 96%

Top Learners:
1. Krunal Sharma - 96%
2. Priya Verma - 92%
3. Amit Kumar - 88%

Struggling Learners:
- 5 learners < 50% on Module 3
- Suggested: Additional support session
```

**Per Learner:**
- Course progress
- Time spent
- Quiz scores
- Engagement level
- Areas of difficulty
- Recommended interventions

#### G. Training Calendar

**View Modes:**
- Daily / Weekly / Monthly
- By trainer
- By department
- By course
- Conflict detection

**Auto-scheduling:**
- New joiner onboarding (Day 1, 3, 7)
- Compliance refresh (Annual)
- Department-wise weekly
- Skill development sessions

#### H. Feedback & Improvement

**Course Feedback:**
- Star rating (1-5)
- What worked well
- What needs improvement
- Suggested topics
- Trainer rating
- NPS score

**Trainer Self-Assessment:**
- Sessions conducted
- Learner satisfaction
- Improvement areas
- Skill development plan

#### I. Certification Management

**Trainer Privileges:**
- Issue certificates
- Set expiry rules
- Re-certification programs
- Bulk certificate generation
- Verify certificates

#### J. Resource Library

**Trainer Tools:**
- Reusable lesson templates
- Question banks (shared)
- Image/video assets
- Presentation templates
- Quiz templates
- Activity templates

#### K. Internal Trainer Marketplace

**Find Internal Trainers:**
- Browse trainers by skill
- Book trainer for team
- Trainer ratings & reviews
- Specialization tags
- Availability calendar

**For Trainers:**
- Showcase expertise
- Manage availability
- Get bookings
- Track engagement

---

### Trainer Workflows

#### 1. Course Creation Workflow

```
Trainer logs in
    ↓
Click "Create New Course"
    ↓
Fill course metadata:
- Title, description
- Department, category
- Target audience
- Estimated duration
- Difficulty level
    ↓
Add modules
    ↓
Add lessons to each module
- Upload videos
- Add PDFs
- Write articles
- Embed external content
    ↓
Create quizzes per module
    ↓
Design final exam
- Select questions from bank
- Or create new questions
- Set rules & timing
    ↓
Save as Draft
    ↓
Submit for Review (if junior)
OR
Publish directly (if senior)
    ↓
Course Live
    ↓
Auto-assign to relevant employees
```

#### 2. Live Training Workflow

```
Schedule session
    ↓
Send invites
    ↓
Participants enroll
    ↓
[Day of training]
    ↓
Pre-session reminder
    ↓
Trainer starts session
    ↓
Mark attendance (QR/manual)
    ↓
Conduct training
- Present content
- Live polls
- Q&A
- Hands-on activities
    ↓
End session
    ↓
Auto-record uploaded
    ↓
Send post-session quiz
    ↓
Collect feedback
    ↓
Update completion status
    ↓
Trainer report generated
```

#### 3. Question Creation Workflow

```
Trainer goes to Question Bank
    ↓
Choose: Single / Bulk Import
    ↓
[Single Creation]
- Select topic
- Type question
- Add options
- Mark correct answer
- Add explanation
- Set difficulty
- Save
    ↓
[Bulk Import]
- Download CSV template
- Fill questions in Excel
- Upload CSV
- System validates
- Preview & confirm
- Bulk save
    ↓
Questions available in bank
    ↓
Use in exams
```

---

### Database Schema (Trainer Module)

```sql
-- Trainer profiles
trainers (
  id, employee_id, type (internal/external),
  expertise_areas, bio, photo_url,
  rating, total_sessions, total_courses,
  hourly_rate (for external),
  status, joined_at
)

-- Trainer specializations
trainer_specializations (
  trainer_id, specialization, certification_url
)

-- Training sessions
training_sessions (
  id, title, description, trainer_id,
  course_id, type (online/offline/hybrid),
  scheduled_start, scheduled_end,
  meeting_url, location,
  capacity, recurring_pattern,
  status (scheduled/ongoing/completed/cancelled),
  recording_url
)

session_participants (
  id, session_id, employee_id,
  registration_status, attended,
  attended_at, feedback_rating,
  feedback_text
)

-- Trainer reviews
trainer_reviews (
  id, trainer_id, employee_id,
  course_id, session_id,
  rating, review_text,
  created_at
)

-- Course approval workflow
course_approvals (
  id, course_id, submitted_by,
  reviewed_by, status,
  comments, submitted_at, reviewed_at
)

-- Training calendar
training_calendar (
  id, trainer_id, date,
  available_slots, booked_slots
)

-- External trainers
external_trainers (
  id, trainer_id, agency,
  contract_start, contract_end,
  payment_terms, total_paid
)

-- Reusable templates
lesson_templates (
  id, name, content_structure,
  created_by, is_public
)

quiz_templates (
  id, name, questions_count,
  difficulty_distribution,
  created_by, is_public
)

-- Trainer analytics
trainer_metrics (
  id, trainer_id, period_month,
  courses_created, sessions_conducted,
  total_learners, avg_rating,
  total_hours, completion_rate
)
```

### API Endpoints (Trainer Module)

```
# Trainer Profile
GET  /trainers                         → All trainers
GET  /trainers/{id}                    → Trainer profile
PUT  /trainers/me                      → Update profile
POST /trainers/me/availability         → Set availability

# Course Creation
POST /trainer/courses                  → Create course
PUT  /trainer/courses/{id}             → Update
POST /trainer/courses/{id}/submit      → Submit for review
POST /trainer/courses/{id}/publish     → Publish (if authorized)
GET  /trainer/courses/my               → My courses

# Content Upload
POST /trainer/upload/video             → Video upload
POST /trainer/upload/pdf               → PDF upload
POST /trainer/upload/image             → Image
GET  /trainer/media/library            → My media

# Question Bank
POST /trainer/questions                → Create question
POST /trainer/questions/bulk-import    → CSV import
GET  /trainer/questions/templates      → Templates
PUT  /trainer/questions/{id}           → Update

# Training Sessions
POST /trainer/sessions                 → Schedule session
GET  /trainer/sessions/upcoming        → My upcoming
POST /trainer/sessions/{id}/start      → Start session
POST /trainer/sessions/{id}/end        → End session
POST /trainer/sessions/{id}/attendance → Mark attendance
POST /trainer/sessions/{id}/recording  → Upload recording

# Analytics
GET  /trainer/analytics/me             → My analytics
GET  /trainer/analytics/course/{id}    → Course analytics
GET  /trainer/analytics/learners       → Learner insights

# Approvals (Head Trainer)
GET  /trainer/approvals/pending        → Courses for review
POST /trainer/approvals/{id}/approve   → Approve
POST /trainer/approvals/{id}/reject    → Reject with comments

# Internal Trainer Marketplace
GET  /trainers/marketplace             → Browse trainers
POST /trainers/{id}/book               → Book trainer
GET  /trainers/{id}/reviews            → Reviews

# Reports
GET  /trainer/reports/sessions         → Session reports
GET  /trainer/reports/courses          → Course reports
GET  /trainer/reports/learners         → Learner progress
```

---

### Mobile UI Flow (Trainer)

#### Trainer Home

```
┌──────────────────────────────┐
│  Trainer Dashboard 👨‍🏫      │
├──────────────────────────────┤
│  📊 This Month:              │
│  Sessions: 24 / Courses: 2   │
│  Learners: 245 / ⭐ 4.5      │
├──────────────────────────────┤
│  Quick Actions:              │
│  [+ New Course]              │
│  [+ Add Question]            │
│  [+ Schedule Session]        │
├──────────────────────────────┤
│  📅 Today's Sessions:        │
│  10:00 AM - API Basics       │
│  📍 Conf Room A | 12 enrolled│
│  [Start Session]             │
│                              │
│  3:00 PM - POSH Refresh      │
│  💻 Online | 45 enrolled     │
│  [Start Online]              │
├──────────────────────────────┤
│  📋 Pending:                 │
│  • Review 3 questions        │
│  • Update Banking course     │
│  • Approve 1 submission      │
└──────────────────────────────┘
```

#### Course Builder (Mobile)

```
┌──────────────────────────────┐
│  ← Course Builder            │
│  Banking API Integration     │
├──────────────────────────────┤
│  📑 Module 1: Introduction   │
│  📊 5 lessons | 45 min       │
│  [Edit] [Preview]            │
│                              │
│  📑 Module 2: Auth           │
│  📊 4 lessons | 60 min       │
│  [Edit] [Preview]            │
│                              │
│  [+ Add Module]              │
├──────────────────────────────┤
│  Course Stats:               │
│  Total Duration: 4 hrs       │
│  Total Lessons: 18           │
│  Total Quizzes: 6            │
├──────────────────────────────┤
│  Status: Draft               │
│  [Save] [Submit for Review]  │
└──────────────────────────────┘
```

---

### Integration Between LMS, Exams & Trainer

```
┌─────────────────────────────────────────┐
│              TRAINER                    │
│  Creates: Courses, Questions, Exams     │
│  Conducts: Live Sessions                │
│  Reviews: Learner Performance           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│                LMS                      │
│  Hosts: Courses, Resources              │
│  Tracks: Progress, Completion           │
│  Recommends: Based on role/dept         │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│            EXAMINATION                  │
│  Conducts: MCQ tests                    │
│  Grades: Auto-evaluation                │
│  Issues: Certificates                   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│              EMPLOYEE                   │
│  Learns → Tested → Certified            │
│  Goes to: HR record, Performance        │
│            Review, Promotion            │
└─────────────────────────────────────────┘
```

### Phased Rollout (LMS + Exams + Trainer)

#### Phase 1: Basic LMS (4 weeks)
- Course creation (basic)
- Video/PDF upload
- Lesson consumption
- Progress tracking
- Mobile-first viewing

#### Phase 2: Examination System (4 weeks)
- Question bank
- MCQ exam engine
- Auto-evaluation
- Result generation
- Basic anti-cheating

#### Phase 3: Advanced Features (4 weeks)
- Learning paths
- Certificates with QR
- Department-wise exams
- Compliance tracking
- Bulk question import

#### Phase 4: Trainer Module (4 weeks)
- Trainer profiles
- Live session scheduling
- Recording management
- Trainer analytics
- Internal marketplace

#### Phase 5: Polish & Scale
- Advanced anti-cheating
- Multi-language
- Offline mode
- Advanced analytics
- ROI tracking

### Use Cases for Your Stack

Aapke fintech/banking integration background ke liye specific examples:

**1. New Joiner Onboarding (IT)**
- Banking API basics course
- Company tools training (Jira, GitHub, AWS)
- Code review standards
- Final assessment → Production access granted

**2. Compliance Mandatory Training**
- POSH (annual)
- Information Security (annual)
- Data Privacy (DPDP Act)
- Banking regulations
- AML/KYC awareness

**3. Field Force Training**
- Verification process certification
- Customer interaction
- Mobile app proficiency
- Safety protocols
- Re-certification every 2 years

**4. Sales Team Enablement**
- Product knowledge (Banking APIs, Payment Gateways)
- Pitch certification
- Competitor intelligence
- CRM proficiency
- Quarterly refresh

**5. Promotion Readiness**
- L1 → L2: Technical depth + soft skills
- L2 → L3: Leadership + system design
- L3 → L4: Strategy + people management
- Final exam = promotion eligibility

---

## 17. Super Admin & Admin Web Portal (React)

### Purpose

Dedicated **React web application** for system administrators (Super Admin and Admin roles). Built separately from Flutter app because:

- Web is better for complex tables, data management
- Mouse + keyboard ideal for configuration tasks
- Large screens needed for analytics dashboards
- Faster development of admin-specific UI

### Why React (Not Flutter Web for Admin)?

| Aspect | Flutter Web | React Web |
|--------|-------------|-----------|
| Complex tables | ⚠️ Limited libraries | ✅ TanStack Table |
| Data grids | ⚠️ Basic | ✅ AG Grid, DataGrid |
| Form handling | ⚠️ OK | ✅ React Hook Form |
| Admin UI libraries | ⚠️ Few | ✅ shadcn, MUI, Ant Design |
| SEO | ❌ Bad | ✅ Native |
| Initial load | ⚠️ Heavy | ✅ Lighter |
| Dev ecosystem | ⚠️ Smaller | ✅ Massive |

### Tech Stack (React Admin)

```
Framework: React 18+ with Vite (fast dev)
Language: TypeScript (type safety)
State: Zustand (lightweight) or Redux Toolkit
UI: shadcn/ui + Tailwind CSS (modern, customizable)
Tables: TanStack Table v8 (best in class)
Forms: React Hook Form + Zod (validation)
Routing: React Router v6
Data: TanStack Query (server state)
Charts: Recharts (declarative)
Icons: Lucide React
Date: date-fns
HTTP: Axios with interceptors
Auth: JWT in httpOnly cookies (more secure)
```

### Folder Structure

```
hrms_admin_web/
├── src/
│   ├── main.tsx                      # Entry point
│   ├── App.tsx                       # Root component
│   │
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts             # Axios setup
│   │   │   ├── auth.ts
│   │   │   ├── users.ts
│   │   │   ├── permissions.ts
│   │   │   └── ...
│   │   ├── utils.ts                  # Utility functions
│   │   ├── validators.ts             # Zod schemas
│   │   └── constants.ts
│   │
│   ├── components/
│   │   ├── ui/                       # shadcn components
│   │   │   ├── button.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── table.tsx
│   │   │   └── ...
│   │   ├── layouts/
│   │   │   ├── AdminLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Footer.tsx
│   │   ├── shared/
│   │   │   ├── DataTable.tsx
│   │   │   ├── PageHeader.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   └── PermissionGate.tsx
│   │   └── auth/
│   │       └── ProtectedRoute.tsx
│   │
│   ├── features/
│   │   ├── super-admin/              # Super Admin only
│   │   │   ├── SystemConfig.tsx
│   │   │   ├── ModuleManagement.tsx
│   │   │   ├── PermissionCatalog.tsx
│   │   │   ├── RoleBuilder.tsx
│   │   │   ├── AdminPermissions.tsx
│   │   │   ├── DatabaseBackup.tsx
│   │   │   ├── ApiKeys.tsx
│   │   │   └── AuditLogs.tsx
│   │   │
│   │   ├── admin/                    # Admin features
│   │   │   ├── UserManagement.tsx
│   │   │   ├── DepartmentManagement.tsx
│   │   │   ├── DesignationManagement.tsx
│   │   │   ├── HolidayCalendar.tsx
│   │   │   ├── ShiftManagement.tsx
│   │   │   ├── PolicyManagement.tsx
│   │   │   └── BulkOperations.tsx
│   │   │
│   │   ├── employees/
│   │   │   ├── EmployeeList.tsx
│   │   │   ├── EmployeeDetail.tsx
│   │   │   ├── EmployeeCreate.tsx
│   │   │   ├── EmployeeEdit.tsx
│   │   │   └── BulkImport.tsx
│   │   │
│   │   ├── reports/
│   │   │   ├── EmployeeReports.tsx
│   │   │   ├── PayrollReports.tsx
│   │   │   ├── ComplianceReports.tsx
│   │   │   ├── AttendanceReports.tsx
│   │   │   └── CustomReportBuilder.tsx
│   │   │
│   │   └── dashboard/
│   │       ├── SuperAdminDashboard.tsx
│   │       ├── AdminDashboard.tsx
│   │       └── widgets/
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── usePermission.ts
│   │   ├── useDebounce.ts
│   │   └── ...
│   │
│   ├── store/
│   │   ├── authStore.ts              # Zustand stores
│   │   ├── userStore.ts
│   │   └── ...
│   │
│   ├── types/
│   │   ├── auth.ts
│   │   ├── user.ts
│   │   └── api.ts
│   │
│   └── router/
│       └── routes.tsx
│
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── vite.config.ts
└── .env
```

### Super Admin Features (Web Only)

#### A. System Configuration

```
Settings → System
─────────────────
General
├─ Company name, logo, branding
├─ Default timezone
├─ Date format
└─ Currency

Email Configuration
├─ SMTP settings
├─ Email templates
└─ Test email

SMS Configuration
├─ Provider (Twilio, MSG91, etc.)
├─ API credentials
└─ Templates

Storage
├─ S3 / MinIO config
├─ Buckets management
└─ Storage usage

Database
├─ Connection status
├─ Backup schedule
├─ Restore points
└─ Manual backup
```

#### B. Permission Management

The most powerful feature - **dynamic permission system:**

```
Permission Catalog
─────────────────
Categories:
├─ Employee Management
│   ├─ employee.view.all       [Visible to: Super Admin, Director, HR]
│   ├─ employee.view.team      [Visible to: Manager]
│   ├─ employee.create         [Visible to: HR, Admin (if granted)]
│   └─ ...
├─ Payroll
│   ├─ payroll.run             [Visible to: HR (if granted)]
│   ├─ salary.view.all         [Visible to: Director, HR]
│   └─ ...
├─ System
│   ├─ system.config           [Super Admin only]
│   ├─ role.create             [Super Admin only]
│   └─ ...

[+ Create New Permission]
```

#### C. Role Builder

```
Roles → Create Custom Role
─────────────────────────
Role Name: [Senior HR Manager]
Description: [HR Manager with extra payroll permissions]
Level: [4]

Inherit From: [HR Manager Template ▼]

Permissions:
☑ All HR Manager permissions
☑ payroll.run
☑ salary.view.all
☐ system.config
☐ role.create

Apply to: [Specific users / All users with designation]

[Create Role]
```

#### D. Admin Permissions Management

**Critical feature** - Super Admin defines what each Admin can do:

```
Admin: rohit@company.com
─────────────────────────
Department: HR Operations

Granted Permissions:
☑ User Management
  ☑ Create employees
  ☑ Edit employees
  ☐ Delete employees
  ☑ Reset passwords
  ☑ Activate/deactivate

☑ Configuration
  ☑ Holiday calendar
  ☑ Department structure
  ☐ Designations
  ☐ Shift management

☐ Payroll
  ☐ Run payroll
  ☐ View salaries

☑ Reports
  ☑ All employee reports
  ☑ Department analytics
  ☐ Compliance reports

[Save Permissions]
```

#### E. Module Management

Enable/disable modules per company:

```
Modules
─────────────────
Core Modules (Always On):
✅ Authentication
✅ Employee Management
✅ Attendance
✅ Leave Management

Optional Modules:
☑ Daily Work Planning      [Configure]
☑ Payroll                  [Configure]
☑ Justice Portal           [Configure]
☑ Field Force              [Configure]
☐ LMS & Examinations       [Enable]
☐ Trainer Module           [Enable]
☐ Performance Mgmt         [Enable]
☐ Asset Management         [Enable]

[Save Configuration]
```

#### F. Audit Logs

```
Audit Logs
─────────────────
Filters: [User] [Action] [Date Range] [Module]

Date          User          Action              Entity        Details
2026-04-30    rohit@hr      employee.created    EMP-1234      View
2026-04-30    super@admin   permission.assign   USR-5678      View
2026-04-30    director@co   salary.view         EMP-1234      View
2026-04-30    krunal@dev    leave.applied       LEAVE-2345    View

[Export to Excel] [Export to PDF]
```

#### G. White-Labeling (Multi-Tenant Ready)

```
Branding
─────────────────
Company Logo: [Upload]
Primary Color: [#2563EB]
Secondary Color: [#10B981]

Login Page
├─ Background image
├─ Welcome text
└─ Custom domain

Email Templates
├─ Header logo
├─ Footer text
└─ Color scheme

Mobile App
├─ App name override
├─ App icon override
└─ Splash screen
```

### Admin Features (Configurable)

Based on permissions granted by Super Admin:

#### A. User Management

- Bulk import (CSV/Excel)
- Bulk update
- Bulk deactivate
- Password reset
- Force logout
- Export user list

#### B. Master Data

- Department CRUD
- Designation CRUD
- Holiday calendar
- Shift definitions
- Leave policies
- Salary components

#### C. Reports & Analytics

- Pre-built reports
- Custom report builder
- Scheduled reports (auto-email)
- Export to Excel/PDF
- Drill-down dashboards

#### D. Bulk Operations

- Bulk leave approval
- Bulk attendance regularization
- Bulk salary updates
- Bulk role assignment

### React Admin Specific APIs

Different endpoints for admin operations:

```
# System (Super Admin only)
GET  /admin/system/config
PUT  /admin/system/config
GET  /admin/system/health
POST /admin/system/backup
GET  /admin/system/logs

# Permission Management (Super Admin only)
GET  /admin/permissions               # All permissions
POST /admin/permissions               # Create permission
GET  /admin/roles                     # All roles
POST /admin/roles                     # Create custom role
PUT  /admin/roles/{id}/permissions    # Update role permissions
POST /admin/users/{id}/role           # Assign role
POST /admin/users/{id}/permissions    # Custom permissions

# Admin Management (Super Admin only)
GET  /admin/admins                    # List admins
POST /admin/admins                    # Create admin
PUT  /admin/admins/{id}/permissions   # Set admin permissions
DELETE /admin/admins/{id}             # Remove admin

# Module Management (Super Admin only)
GET  /admin/modules
PUT  /admin/modules/{id}/enable
PUT  /admin/modules/{id}/configure

# Audit Logs
GET  /admin/audit-logs
GET  /admin/audit-logs/export

# Bulk Operations
POST /admin/bulk/employees/import
POST /admin/bulk/employees/update
POST /admin/bulk/leaves/approve
POST /admin/bulk/users/deactivate

# White-Labeling
GET  /admin/branding
PUT  /admin/branding
```

### Authentication Differences

React admin uses **httpOnly cookies** for security:

```typescript
// More secure than localStorage for admin
// CSRF protection required
// Session-based with refresh

// Login
POST /auth/admin/login
→ Sets httpOnly cookies
→ Returns user info (no token in body)

// Subsequent requests
→ Browser auto-sends cookies
→ Server validates session

// Logout
POST /auth/admin/logout
→ Clears cookies
```

### Database Changes

New tables needed:

```sql
-- Super Admin specific
super_admins (
  id, user_id, can_be_deleted_by,
  created_at, last_action_at
)

-- Custom permissions
custom_permissions (
  id, code, description, category,
  created_by, created_at
)

-- Custom roles
custom_roles (
  id, name, level, base_role_id,
  description, is_active, created_by
)

-- User-specific permissions (overrides role)
user_permissions (
  id, user_id, permission_id,
  granted_by, granted_at, expires_at
)

-- Module management
modules (
  id, name, code, is_core,
  is_enabled, config_json
)

-- White-labeling
branding (
  id, company_id, logo_url,
  primary_color, secondary_color,
  custom_domain, email_template
)

-- Audit logs (already exists, enhanced)
audit_logs (
  id, user_id, action, entity_type,
  entity_id, old_value, new_value,
  ip_address, user_agent, created_at,
  source (web/mobile)
)
```

---

## 18. Flutter Multi-Platform Setup

### Strategy

**Single Flutter codebase** runs on:
- Android (mobile)
- iOS (mobile)
- Web (desktop browser)

This works because Flutter compiles to native for each platform.

### Platform-Specific Considerations

#### Mobile Features (Android + iOS)

✅ **Always available:**
- Camera (selfie attendance)
- GPS (geo-fencing)
- Biometric (Face ID, Fingerprint)
- Push notifications (FCM)
- File picker
- Offline storage
- Background tasks

#### Web-Specific Adaptations

⚠️ **Different behavior on Flutter Web:**
- Camera → Use device camera via web API (limited)
- GPS → HTML5 Geolocation API
- Biometric → Not available, fallback to password
- Push → Web push (Firebase)
- Offline → Browser localStorage / IndexedDB
- File upload → Standard HTML file input

### Responsive Design

```dart
// Use LayoutBuilder for adaptive UI
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < 600) {
      return MobileLayout();   // Phone
    } else if (constraints.maxWidth < 1024) {
      return TabletLayout();   // Tablet
    } else {
      return DesktopLayout();  // Desktop / Web
    }
  },
)
```

### Folder Structure (Updated)

```
hrms_mobile/
├── lib/
│   ├── main.dart
│   ├── main_mobile.dart        # Mobile-specific entry
│   ├── main_web.dart           # Web-specific entry
│   │
│   ├── core/
│   │   ├── platform/
│   │   │   ├── platform_check.dart      # isWeb, isMobile, isIOS
│   │   │   ├── camera_service.dart      # Conditional implementation
│   │   │   ├── location_service.dart
│   │   │   └── biometric_service.dart
│   │   └── ...
│   │
│   ├── features/
│   │   └── (same as before)
│   │
│   └── shared/
│       └── widgets/
│           ├── adaptive/
│           │   ├── adaptive_scaffold.dart
│           │   ├── adaptive_navigation.dart
│           │   └── adaptive_dialog.dart
│           └── ...
│
├── web/                         # Flutter web specific
│   ├── index.html
│   ├── manifest.json
│   └── icons/
│
├── ios/                         # iOS native config
├── android/                     # Android native config
└── pubspec.yaml
```

### Build Commands

```bash
# Android
flutter build apk --release
flutter build appbundle --release

# iOS
flutter build ios --release
flutter build ipa --release

# Web
flutter build web --release
flutter build web --web-renderer canvaskit  # Better quality
flutter build web --web-renderer html       # Better SEO

# Run
flutter run -d chrome       # Web
flutter run -d windows      # Windows desktop (optional)
flutter run                 # Mobile (auto-detect)
```

### Web Hosting

Flutter Web build output can be hosted on:
- Vercel
- Netlify
- Firebase Hosting
- AWS S3 + CloudFront
- Same backend server (FastAPI static files)

### iOS Setup Requirements

For iOS development:
- Mac required (for Xcode)
- Apple Developer account ($99/year)
- iOS Simulator
- Device testing
- TestFlight for beta
- App Store submission

### Push Notifications (Cross-Platform)

```dart
// Firebase Cloud Messaging works on all platforms
import 'package:firebase_messaging/firebase_messaging.dart';

// Same code for Android, iOS, and Web
FirebaseMessaging.instance.getToken();
FirebaseMessaging.onMessage.listen(handleMessage);
```

### Conditional Code

```dart
// Platform-specific imports
import 'package:flutter/foundation.dart' show kIsWeb;

if (kIsWeb) {
  // Web-specific code
} else if (Platform.isIOS) {
  // iOS-specific
} else if (Platform.isAndroid) {
  // Android-specific
}
```

### Testing Strategy

| Platform | Testing |
|----------|---------|
| Android | Real devices + emulator |
| iOS | Real devices + simulator (Mac only) |
| Web | Chrome, Safari, Firefox, Edge |

### Performance Considerations

- **Mobile:** Optimize images, lazy loading
- **Web:** Code splitting, deferred loading
- **iOS:** Memory management critical
- **Android:** Battery optimization

---

**Document Version:** 1.0
**Last Updated:** April 2026
**Author:** Krunal (with Claude)
