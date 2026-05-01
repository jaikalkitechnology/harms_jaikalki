# Phase 2: Employee Management - Jaikalki HRMS

**Duration:** 5-7 days
**Hours:** 70 (increased from 60 due to salary templates)
**Priority:** CRITICAL
**Depends on:** Phase 1 (Auth)

---

## Objective

Build complete employee management system - profiles, documents, departments, designations, organizational hierarchy. Includes **Jaikalki specific salary templates** for different employee categories.

## Deliverables

- ✅ Employee CRUD with role-based access
- ✅ Employee profile (full details)
- ✅ Document management (upload, view, verify)
- ✅ Department & designation management
- ✅ Reporting hierarchy
- ✅ Org chart visualization
- ✅ Employee directory (mobile)
- ✅ Self-service profile editing
- ✅ **Salary templates per position category**
- ✅ **Employee categories: Intern, Trainee, Permanent, Contract**
- ✅ **6-month probation tracking**
- ✅ **Intern travel expense management**

---

## Reference Documents

- HRMS_Architecture.md → Section 3 (Database Schema)
- **SALARY_STRUCTURE_JAIKALKI.md** (entire document)

---

## Tasks

### Task 2.1: Database Models with Jaikalki Categories (6h)

**`app/models/employee_category.py`:**
```python
class EmployeeCategory(Base):
    __tablename__ = 'employee_categories'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)  # INTERN, TRAINEE, PERMANENT, CONTRACT
    name = Column(String(50), nullable=False)
    description = Column(Text)

    # Eligibility
    eligible_for_pf = Column(Boolean, default=True)
    eligible_for_esic = Column(Boolean, default=True)
    eligible_for_gratuity = Column(Boolean, default=False)
    eligible_for_pl = Column(Boolean, default=False)
    eligible_for_bonus = Column(Boolean, default=False)

    # Pay structure
    has_salary = Column(Boolean, default=True)
    has_stipend = Column(Boolean, default=False)
    only_travel_expense = Column(Boolean, default=False)

    # Probation
    requires_probation = Column(Boolean, default=True)
    default_probation_months = Column(Integer, default=6)

    is_active = Column(Boolean, default=True)
```

**`app/models/employee.py`:**
```python
class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    employee_code = Column(String(20), unique=True)  # JKT001, JKT014, etc.

    # Personal
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    blood_group = Column(String(10))

    # Employment
    category_id = Column(Integer, ForeignKey('employee_categories.id'))
    designation_id = Column(Integer, ForeignKey('designations.id'))
    department_id = Column(Integer, ForeignKey('departments.id'))
    reporting_to = Column(Integer, ForeignKey('employees.id'))

    # Dates
    date_of_joining = Column(Date)
    probation_end_date = Column(Date, nullable=True)
    confirmation_date = Column(Date, nullable=True)
    exit_date = Column(Date, nullable=True)

    # Salary template applied
    salary_template_id = Column(Integer, ForeignKey('salary_templates.id'))
    ctc_annual = Column(Numeric(12, 2), default=0)

    # Work
    work_location = Column(String(200), default='Mira Road, Thane')
    employment_type = Column(String(50))  # full_time, part_time, contract
    work_mode = Column(String(20))  # office, wfh, hybrid

    # Status
    status = Column(String(20), default='active')  # active, on_notice, exited
    is_on_probation = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
```

**`app/models/salary_template.py`:**
```python
class SalaryTemplate(Base):
    __tablename__ = 'salary_templates'

    id = Column(Integer, primary_key=True)
    template_code = Column(String(50), unique=True)
    template_name = Column(String(100))
    category = Column(Enum('intern', 'trainee', 'permanent', 'contract'))
    designation_level = Column(Integer)

    # Salary components (monthly)
    basic_amount = Column(Numeric(10, 2), default=0)
    basic_percentage = Column(Numeric(5, 2), default=50)

    hra_amount = Column(Numeric(10, 2), default=0)
    hra_percentage = Column(Numeric(5, 2), default=30)

    other_allowance = Column(Numeric(10, 2), default=0)
    special_allowance = Column(Numeric(10, 2), default=0)
    conveyance = Column(Numeric(10, 2), default=0)
    medical_allowance = Column(Numeric(10, 2), default=0)
    lta = Column(Numeric(10, 2), default=0)
    food_coupon = Column(Numeric(10, 2), default=0)

    # For interns
    travel_expense_max = Column(Numeric(10, 2), default=0)
    is_paid_internship = Column(Boolean, default=False)

    # Probation
    has_probation = Column(Boolean, default=True)
    probation_months = Column(Integer, default=6)
    probation_extension_months = Column(Integer, default=2)

    # Insurance
    mediclaim_amount = Column(Numeric(10, 2), default=200000)
    pa_insurance_amount = Column(Numeric(10, 2), default=500000)

    # Notice periods
    notice_period_probation = Column(Integer, default=15)
    notice_period_confirmed = Column(Integer, default=30)
    notice_period_termination = Column(Integer, default=7)

    is_active = Column(Boolean, default=True)
```

**`app/models/employee_probation.py`:**
```python
class EmployeeProbation(Base):
    __tablename__ = 'employee_probation'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    probation_start_date = Column(Date, nullable=False)
    probation_end_date = Column(Date, nullable=False)
    is_extended = Column(Boolean, default=False)
    extension_end_date = Column(Date, nullable=True)
    extension_reason = Column(Text)
    status = Column(Enum('in_progress', 'extended', 'confirmed', 'terminated'))
    confirmed_date = Column(Date, nullable=True)
    confirmation_letter_url = Column(String(500))
    confirmed_by = Column(Integer, ForeignKey('users.id'))
    monthly_reviews = Column(JSON)  # Performance reviews during probation
```

**`app/models/intern_travel_expense.py`:**
```python
class InternTravelExpense(Base):
    __tablename__ = 'intern_travel_expenses'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    expense_date = Column(Date, nullable=False)
    expense_type = Column(Enum('local_travel', 'office_commute', 'project_visit'))
    amount = Column(Numeric(10, 2), nullable=False)
    receipt_url = Column(String(500))
    description = Column(Text)
    status = Column(Enum('pending', 'approved', 'rejected', 'reimbursed'))
    approved_by = Column(Integer, ForeignKey('users.id'))
    approved_at = Column(DateTime, nullable=True)
    reimbursed_at = Column(DateTime, nullable=True)
```

**Plus existing models:**
- EmployeeDocument
- EmployeeAddress
- EmployeeBankDetails
- EmergencyContact
- FamilyMember

### Task 2.2: Migrations & Seed Data (4h)

**Categories Seed:**
```python
categories = [
    ('INTERN', 'Intern', False, False, False, True, False, 0, 6, 'Travel expense only'),
    ('TRAINEE', 'Trainee', True, True, False, False, False, 1, 6, 'With probation'),
    ('PERMANENT', 'Permanent', True, True, True, False, False, 1, 6, 'Confirmed employee'),
    ('CONTRACT', 'Contract', True, False, False, False, False, 0, 0, 'Contract employee'),
]
```

**Salary Templates Seed (8 templates from SALARY_STRUCTURE_JAIKALKI.md):**

1. **JKT-INTERN-001** - Intern (Travel expense only)
2. **JKT-TRAINEE-L1** - Junior Developer/Trainee (Pooja's exact structure)
3. **JKT-PERM-L2** - Mid-Level Developer
4. **JKT-PERM-L3** - Tech Lead
5. **JKT-PERM-L4** - Manager
6. **JKT-PERM-L5** - Director/VP
7. **JKT-FIELD-L1** - Field Sales Executive
8. **JKT-HOUSE-L1** - Housekeeping Staff

**Departments:**
- IT (Pooja's department)
- Sales
- HR
- Admin
- Operations

**Sample Employees:**
- JKT001 - Director (Sample)
- JKT014 - Pooja Kumawat (Front-end Developer Flutter, Trainee category)
- JKT015 - Sample HR
- JKT016 - Sample Manager
- JKT017 - Sample Intern

### Task 2.3: Salary Calculator Service (5h)

**`app/services/salary_calculator.py`:**

Implement `JaikalkiSalaryCalculator` class as defined in SALARY_STRUCTURE_JAIKALKI.md:
- `calculate_from_template(template_id, ctc_annual)` 
- `_intern_structure(template)` - For interns (no salary)
- `_calculate_breakup(ctc_monthly, template)` - Standard calculation
- `_calculate_pt(gross_monthly)` - Maharashtra PT
- PF calculation (12% employee, 13% employer with admin charges)
- ESIC calculation (0.75% employee, 3.25% employer if gross ≤ 21000)

### Task 2.4: Employee Schemas (3h)

`app/schemas/employee.py`:
- `EmployeeCreate` - Includes category_id, salary_template_id, ctc_annual
- `EmployeeUpdate`
- `EmployeeOut` (full details)
- `EmployeeListItem` (lightweight)
- `EmployeeProfile` (self-view)
- `SalaryTemplateOut`
- `SalaryBreakupOut` - Calculated breakup
- `InternTravelExpenseCreate`
- `ProbationStatusOut`

### Task 2.5: Employee Service (5h)

`app/services/employee_service.py`:
- `create_employee(data, current_user)`:
  - Generate employee code (JKT + sequence)
  - Apply salary template
  - Calculate breakup
  - Create probation record (if applicable)
  - For interns: skip probation, only travel expense setup
- `update_employee(id, data)`
- `get_employee(id, current_user)` - Permission-aware
- `list_employees(current_user, filters)` - Scope-based
- `delete_employee(id)` - Soft delete
- `assign_manager(employee_id, manager_id)`
- `transfer_department(employee_id, dept_id)`
- `confirm_employee(employee_id)` - End probation
- `extend_probation(employee_id, months, reason)`

### Task 2.6: Employee API Endpoints (5h)

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/employees` | `employee.view.team` (filtered) |
| GET | `/employees/{id}` | scoped |
| POST | `/employees` | `employee.create` |
| PUT | `/employees/{id}` | scoped |
| DELETE | `/employees/{id}` | `employee.delete` |
| GET | `/employees/{id}/documents` | scoped |
| POST | `/employees/{id}/documents` | self or HR |
| PUT | `/employees/{id}/manager` | HR |
| GET | `/employees/me` | self |
| PUT | `/employees/me` | self (limited fields) |
| **POST** | **`/employees/{id}/confirm`** | **HR (end probation)** |
| **POST** | **`/employees/{id}/extend-probation`** | **HR** |
| **GET** | **`/employees/probation/expiring`** | **HR (15 days warning)** |

### Task 2.7: Salary Template APIs (3h)

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/salary-templates` | All authenticated |
| GET | `/salary-templates/{id}` | All authenticated |
| GET | `/salary-templates/{id}/calculate?ctc=X` | HR, Admin |
| POST | `/salary-templates` | Super Admin |
| PUT | `/salary-templates/{id}` | Super Admin |

### Task 2.8: Intern Travel Expense APIs (3h)

| Method | Endpoint | Permission |
|--------|----------|------------|
| POST | `/interns/expenses` | Intern self |
| GET | `/interns/expenses/me` | Intern self |
| GET | `/interns/expenses/pending` | HR, Manager |
| POST | `/interns/expenses/{id}/approve` | HR, Manager |
| POST | `/interns/expenses/{id}/reject` | HR, Manager |
| GET | `/interns/expenses/report` | HR |

### Task 2.9: Document Upload (4h)

- Multipart file upload
- Validation (size, type)
- S3/MinIO storage
- Generate signed URLs
- Document types: Aadhaar, PAN, Passport, Education, Experience
- Verification workflow

### Task 2.10: Department & Designation APIs (3h)

CRUD for departments and designations.

### Task 2.11: Org Chart Service (4h)

Build hierarchical tree, get reportees, skip-level access.

### Task 2.12: Backend Tests (4h)

Test scenarios:
- Director sees all employees
- HR sees all employees
- Manager sees only team
- Employee sees only self
- Intern creation: no salary, only travel expense
- Trainee creation: 6-month probation auto-set
- Permanent creation: full salary breakup
- Salary calculator accuracy (matches Pooja's offer letter)
- Probation extension workflow
- Confirmation workflow

### Task 2.13: Flutter - Employee Feature (3h)

```
features/employee/
├── data/
│   ├── models/
│   │   ├── employee_model.dart
│   │   ├── salary_template_model.dart
│   │   └── document_model.dart
│   ├── datasources/
│   └── repositories/
├── domain/
└── presentation/
    ├── bloc/
    └── pages/
        ├── employee_list_page.dart
        ├── employee_detail_page.dart
        ├── profile_page.dart
        ├── edit_profile_page.dart
        ├── org_chart_page.dart
        └── intern_travel_expense_page.dart  # NEW
```

### Task 2.14: Flutter - Employee Directory (5h)

Features same as before + category badge (Intern/Trainee/Permanent).

### Task 2.15: Flutter - Employee Detail (4h)

Show:
- Category badge
- Salary template name
- CTC (if permission)
- Probation status (with days remaining)
- Confirmation status

### Task 2.16: Flutter - Profile Self-Service (5h)

- Edit personal info
- Upload documents
- View probation status
- For interns: Submit travel expense

### Task 2.17: Flutter - Org Chart (4h)

Visual hierarchy.

### Task 2.18: Flutter - Intern Travel Expense Screen (4h)

For intern users only:
- Submit new expense
- Upload receipt photo
- View expense history
- Status tracking (pending/approved/reimbursed)
- Monthly summary

### Task 2.19: Image Upload (3h)

Profile photo, document upload.

---

## Acceptance Criteria

### Backend
- [ ] Director can view all employees
- [ ] HR can view all employees
- [ ] Manager can view only their team
- [ ] Employee can view only self
- [ ] Document upload to S3 works
- [ ] Org chart returns correct hierarchy
- [ ] All permissions enforced
- [ ] **Intern category created without salary**
- [ ] **Trainee gets 6-month probation auto-set**
- [ ] **Salary calculation matches Pooja's offer (CTC 270588)**
- [ ] **Probation expiring report works**
- [ ] **Travel expense workflow for interns works**

### Frontend
- [ ] Employee directory displays correctly
- [ ] Search works
- [ ] Department filter works
- [ ] Employee detail screen shows scoped data
- [ ] Profile self-service editable
- [ ] Photo upload works
- [ ] Org chart visualizes hierarchy
- [ ] **Category badge shows on each employee**
- [ ] **Probation status visible to HR/Manager**
- [ ] **Intern can submit travel expense**

---

## Validation

```bash
# Test salary calculation for Trainee L1 (Pooja's template)
curl http://localhost:8000/v1/salary-templates/2/calculate?ctc=270588 \
  -H "Authorization: Bearer HR_TOKEN"

# Expected response:
# {
#   "basic": 15000,
#   "hra": 4500,
#   "other_allowance": 450,
#   "gross": 19950,
#   "pf_employee": 1800,
#   "esic_employee": 150,
#   "professional_tax": 0,
#   "total_deductions": 1950,
#   "net_salary": 18000,
#   "pf_employer": 1950,
#   "esic_employer": 649,
#   "total_ctc_monthly": 22549,
#   "total_ctc_annual": 270588
# }

# Create intern (no salary, only travel)
curl -X POST http://localhost:8000/v1/employees \
  -H "Authorization: Bearer HR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "Intern",
    "category_code": "INTERN",
    "designation_id": 1,
    "department_id": 1,
    "salary_template_id": 1,
    "date_of_joining": "2026-05-01"
  }'

# Submit intern travel expense
curl -X POST http://localhost:8000/v1/interns/expenses \
  -H "Authorization: Bearer INTERN_TOKEN" \
  -F "amount=150" \
  -F "expense_date=2026-04-30" \
  -F "expense_type=office_commute" \
  -F "receipt=@receipt.jpg"
```

---

## Claude Code Prompt

```
Read these documents:
- HRMS_Architecture.md (sections 3 - Database Schema, 8.1 - Onboarding)
- SALARY_STRUCTURE_JAIKALKI.md (entire file)

Implement Phase 2 (Employee Management) for Jaikalki HRMS as described.

Build a complete employee management system with Jaikalki-specific features:

Backend:
1. Models: Employee, EmployeeCategory, SalaryTemplate, EmployeeProbation, InternTravelExpense
2. Implement JaikalkiSalaryCalculator service exactly matching SALARY_STRUCTURE_JAIKALKI.md
3. 8 default salary templates (Intern, Trainee, L2-L5, Field, Housekeeping)
4. APIs for employee CRUD with category-aware logic
5. Salary template CRUD (Super Admin only)
6. Intern travel expense workflow
7. Probation tracking and confirmation workflow

CRITICAL Jaikalki Requirements:
- Employee codes: JKT001, JKT002... (prefix configurable)
- Interns: NO salary, only travel expense reimbursement
- Trainees/Permanent: 6-month probation default
- Probation can extend 2 more months
- After probation, generate confirmation letter
- Salary calculator must match Pooja's offer letter exactly:
  * Basic: 15,000
  * HRA: 4,500
  * Other: 450
  * Gross: 19,950
  * PF Employee: 1,800
  * ESIC Employee: 150
  * Net: 18,000
  * Total CTC: 22,549/month or 2,70,588/year

Flutter:
- Employee directory with category badges
- Detail page with probation status
- Intern-specific travel expense screen
- Photo capture for receipts

Test with sample data:
- Create JKT014 = Pooja Kumawat (Trainee)
- Create JKT017 = Test Intern (Intern category)
- Verify salary breakup matches offer letter
- Test probation expiry alerts

Run all tests before completing.
```

---

## Next Phase

➡️ **Phase 3: Attendance & Leave Management** (PHASE_03_Attendance_Leave.md)

---

## Tasks

### Task 2.1: Database Models (5h)

**`app/models/employee.py`:**
```python
- Employee (id, user_id, employee_code, first_name, last_name,
            date_of_birth, date_of_joining, designation_id,
            department_id, reporting_to, employment_type,
            work_location, blood_group, status, exit_date)

- EmployeeDocument (id, employee_id, doc_type, file_url,
                   verified, expires_at)

- EmployeeAddress (id, employee_id, type, line1, city,
                  state, pincode, country)

- EmployeeBankDetails (id, employee_id, account_no, ifsc,
                      bank_name, branch)

- EmergencyContact (id, employee_id, name, relation,
                   phone, address)

- FamilyMember (id, employee_id, name, relation, dob,
               is_dependent)
```

### Task 2.2: Migrations & Seed Data (2h)

Create sample data:
- 3 departments (IT, Sales, HR)
- 8 designations (L1-L5)
- 10 sample employees with hierarchy

### Task 2.3: Employee Schemas (3h)

`app/schemas/employee.py`:
- `EmployeeCreate`
- `EmployeeUpdate`
- `EmployeeOut` (full details)
- `EmployeeListItem` (lightweight)
- `EmployeeProfile` (self-view)
- `DocumentUpload`

### Task 2.4: Employee Service (5h)

`app/services/employee_service.py`:
- `create_employee(data)` - HR creates new
- `update_employee(id, data)` - HR/self updates
- `get_employee(id, current_user)` - Permission-aware
- `list_employees(current_user, filters)` - Scope-based
- `delete_employee(id)` - Soft delete
- `assign_manager(employee_id, manager_id)`
- `transfer_department(employee_id, dept_id)`

### Task 2.5: Employee API Endpoints (5h)

`app/api/v1/employees.py`:

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/employees` | `employee.view.team` (filtered) |
| GET | `/employees/{id}` | scoped |
| POST | `/employees` | `employee.create` |
| PUT | `/employees/{id}` | scoped |
| DELETE | `/employees/{id}` | `employee.delete` |
| GET | `/employees/{id}/documents` | scoped |
| POST | `/employees/{id}/documents` | self or HR |
| PUT | `/employees/{id}/manager` | HR |
| GET | `/employees/me` | self |
| PUT | `/employees/me` | self (limited fields) |

### Task 2.6: Document Upload (4h)

- Multipart file upload
- Validation (size, type)
- S3/MinIO storage
- Generate signed URLs
- Document types: Aadhaar, PAN, Passport, Education, Experience
- Verification workflow

### Task 2.7: Department & Designation APIs (3h)

`app/api/v1/organization.py`:
- CRUD for departments
- CRUD for designations
- Department head assignment
- Org chart endpoint

### Task 2.8: Org Chart Service (4h)

`app/services/org_chart_service.py`:
- Build hierarchical tree
- Get reportees (direct + indirect)
- Skip-level access
- Department-wise tree

### Task 2.9: Backend Tests (4h)

Test scenarios:
- Director sees all employees
- HR sees all employees
- Manager sees only team
- Employee sees only self
- Document upload works
- Permission denials
- Search & filters

### Task 2.10: Flutter - Employee Feature (3h)

```
features/employee/
├── data/
│   ├── models/
│   │   ├── employee_model.dart
│   │   └── document_model.dart
│   ├── datasources/
│   └── repositories/
├── domain/
└── presentation/
    ├── bloc/
    │   ├── employee_list_bloc.dart
    │   ├── employee_detail_bloc.dart
    │   └── profile_bloc.dart
    └── pages/
        ├── employee_list_page.dart
        ├── employee_detail_page.dart
        ├── profile_page.dart
        ├── edit_profile_page.dart
        └── org_chart_page.dart
```

### Task 2.11: Flutter - Employee Directory (5h)

Features:
- List all visible employees
- Search by name/email/dept
- Filter by department
- Department grouping
- Employee card (photo, name, designation)
- Tap to view detail
- Pull-to-refresh
- Pagination

### Task 2.12: Flutter - Employee Detail (4h)

Sections:
- Profile photo + basic info
- Contact (email, phone)
- Work info (designation, dept, joining date)
- Reporting manager
- Skills
- Documents (if permission)
- Family (if self/HR)
- Bank details (if self/HR)

### Task 2.13: Flutter - Profile Self-Service (5h)

Employee can edit:
- Personal info (limited)
- Address
- Emergency contact
- Family details
- Profile photo
- Upload documents

### Task 2.14: Flutter - Org Chart (4h)

Visual hierarchy:
- Tree view
- Tap to navigate
- Department filter
- Employee count per dept

### Task 2.15: Image Upload (3h)

- Profile photo upload
- Image picker (camera + gallery)
- Compression
- Upload to backend
- Cache management

---

## Acceptance Criteria

### Backend
- [ ] Director can view all employees
- [ ] HR can view all employees
- [ ] Manager can view only their team
- [ ] Employee can view only self
- [ ] Document upload to S3 works
- [ ] Org chart returns correct hierarchy
- [ ] All permissions enforced

### Frontend
- [ ] Employee directory displays correctly
- [ ] Search works
- [ ] Department filter works
- [ ] Employee detail screen shows scoped data
- [ ] Profile self-service editable
- [ ] Photo upload works
- [ ] Org chart visualizes hierarchy

---

## Validation

```bash
# Get all employees (as Director)
curl http://localhost:8000/v1/employees \
  -H "Authorization: Bearer DIRECTOR_TOKEN"

# Get specific employee
curl http://localhost:8000/v1/employees/1 \
  -H "Authorization: Bearer TOKEN"

# Upload document
curl -X POST http://localhost:8000/v1/employees/1/documents \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@aadhaar.pdf" \
  -F "doc_type=aadhaar"

# Run tests
pytest tests/test_employees.py -v
```

---

## Claude Code Prompt

```
Read HRMS_Architecture.md sections 3 (Database Schema) and 8.1 (Onboarding).

Implement Phase 2 (Employee Management) as described in PHASE_02_Employee.md.

Build a complete employee management system with:
- Backend: Models, services, APIs with proper RBAC
- Document upload to S3/MinIO
- Department & designation management
- Org chart with reporting hierarchy

Flutter:
- Employee directory with search & filters
- Employee detail page with scoped data
- Self-service profile editing
- Photo upload
- Org chart visualization

Ensure all permission scopes work:
- Director/HR: see all
- Manager: see only team
- Employee: see only self

Test thoroughly with different role tokens.
```

---

## Next Phase

➡️ **Phase 3: Attendance & Leave Management** (PHASE_03_Attendance_Leave.md)
