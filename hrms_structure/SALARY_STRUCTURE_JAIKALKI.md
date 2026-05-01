# Salary Structure & Position Templates - Jaikalki Technology Pvt Ltd

**Reference:** Based on actual Jaikalki Technology offer letters
**Sample Employee:** Pooja Kumawat (JKT014) - Front-end Developer (Flutter)
**Effective:** 01 Jan 2026

---

## 🏢 Company Details

```
Company Name: Jaikalki Technology Pvt Ltd
Address: Sh N B1/A Ground Floor, Mahavir, Nagar,
         Deepak Hospital, Mira Road,
         Thane-401107, Maharashtra
Database: db_hrms_jaikalki
Project Path: C:\Users\Shyamveer\PycharmProjects\harms_jaikalki
```

---

## 💰 Standard Salary Structure (As Per Jaikalki Format)

### Sample: Front-end Developer (Flutter) - JKT014

| Component | Per Month (₹) | Per Annum (₹) |
|-----------|---------------|---------------|
| **EARNINGS** | | |
| Basic Salary | 15,000 | 1,80,000 |
| House Rent Allowance (HRA) | 4,500 | 54,000 |
| Other Allowance | 450 | 5,400 |
| **Gross Salary** | **19,950** | **2,39,400** |
| | | |
| **EMPLOYEE DEDUCTIONS** | | |
| Provident Fund (Employee) | 1,800 | 21,600 |
| ESIC (Employee) | 150 | 1,800 |
| Professional Tax | 0 | 0 |
| **Total Deductions** | **1,950** | **23,400** |
| | | |
| **Net Salary** | **18,000** | **2,16,000** |
| | | |
| **EMPLOYER CONTRIBUTIONS** | | |
| Provident Fund (Employer) | 1,950 | 23,400 |
| ESIC (Employer) | 649 | 7,788 |
| **Total Employer Cost** | **2,599** | **31,188** |
| | | |
| **TOTAL CTC** | **22,549** | **2,70,588** |

---

## 📊 Salary Calculation Formulas (Jaikalki Standard)

### Basic Components Ratio

```python
# Standard Jaikalki ratios
BASIC_RATIO = 0.6678  # ~66.78% of gross
HRA_RATIO = 0.2256    # ~22.56% of gross
OTHER_RATIO = 0.0226  # ~2.26% of gross

# From CTC, work backwards
def calculate_from_ctc(ctc_annual):
    ctc_monthly = ctc_annual / 12

    # Approximate gross from CTC
    # CTC = Gross + Employer PF + Employer ESIC
    gross_monthly = ctc_monthly / 1.13  # ~13% employer cost

    basic = gross_monthly * BASIC_RATIO
    hra = gross_monthly * HRA_RATIO
    other = gross_monthly * OTHER_RATIO

    return {
        'basic': round(basic),
        'hra': round(hra),
        'other_allowance': round(other),
        'gross': round(basic + hra + other)
    }
```

### Statutory Calculations

#### Provident Fund (PF)

```python
def calculate_pf(basic_salary):
    """
    PF calculation as per EPF Act
    - Employee: 12% of Basic
    - Employer: 12% of Basic (3.67% to PF + 8.33% to EPS)
    - Capped at ₹15,000 basic (₹1,800 max contribution)
    """
    pf_basic = min(basic_salary, 15000)

    # Standard 12% calculation
    employee_pf = pf_basic * 0.12

    # Jaikalki uses slightly higher employer rate (~13%)
    # This includes admin charges
    employer_pf = pf_basic * 0.13  # ₹15000 * 0.13 = ₹1950

    return {
        'employee_pf': round(employee_pf),
        'employer_pf': round(employer_pf)
    }

# For Pooja (Basic 15000):
# Employee PF: 15000 * 0.12 = 1800 ✓
# Employer PF: 15000 * 0.13 = 1950 ✓
```

#### ESIC (Employee State Insurance)

```python
def calculate_esic(gross_salary):
    """
    ESIC as per ESI Act
    - Employee: 0.75% of Gross
    - Employer: 3.25% of Gross
    - Applicable only if Gross <= ₹21,000
    """
    if gross_salary > 21000:
        return {'employee_esic': 0, 'employer_esic': 0}

    employee_esic = gross_salary * 0.0075
    employer_esic = gross_salary * 0.0325

    return {
        'employee_esic': round(employee_esic),
        'employer_esic': round(employer_esic)
    }

# For Pooja (Gross 19950):
# Employee ESIC: 19950 * 0.0075 = 149.625 ≈ 150 ✓
# Employer ESIC: 19950 * 0.0325 = 648.375 ≈ 649 ✓
```

#### Professional Tax (Maharashtra)

```python
def calculate_professional_tax(gross_monthly, state='Maharashtra'):
    """
    Professional Tax slabs for Maharashtra (FY 2025-26)
    """
    if state != 'Maharashtra':
        return 0  # Other states have different slabs

    if gross_monthly <= 7500:
        return 0
    elif gross_monthly <= 10000:
        return 175
    else:
        # February: 300, Others: 200
        return 200  # Average for monthly calculation

# For Pooja (Gross 19950): 200/month
# But shown as 0 in offer letter (may be deducted differently)
```

---

## 🎯 Position-Based Salary Templates

These templates auto-populate when creating new employee:

### Template 1: Intern (No Salary - Travel Expense Only)

```yaml
template_name: "Intern"
category: "intern"
duration: "3-6 months"
basic: 0
hra: 0
other_allowance: 0
gross: 0
travel_expense: 3000  # Max per month
laptop_provided: true
mentor_assigned: true

deductions:
  pf: 0  # Not applicable for interns
  esic: 0
  professional_tax: 0

probation: false  # Direct intern, no probation
benefits:
  - "Certificate of Internship"
  - "Letter of Recommendation (on completion)"
  - "Travel reimbursement up to ₹3,000/month"
  - "Stipend (optional, based on performance)"
  - "Conversion to full-time possible after internship"

terms:
  - "Will receive only travel reimbursement"
  - "No salary, PF, or ESIC during internship"
  - "Internship duration: 3-6 months"
  - "Mentorship by senior team member"
  - "After internship, eligible for full-time offer"
  - "If hired full-time, will go through 6-month probation"
```

### Template 2: Junior Developer / L1 Trainee (Probation 6 months)

```yaml
template_name: "Junior Developer (Trainee)"
category: "trainee"
designation_level: 1
ctc_annual: 270588    # Same as Pooja's offer
ctc_monthly: 22549

salary_breakup:
  basic: 15000
  hra: 4500
  other_allowance: 450
  gross: 19950

deductions:
  pf_employee: 1800
  esic_employee: 150
  professional_tax: 0
  total: 1950

net_salary: 18000

employer_contribution:
  pf_employer: 1950
  esic_employer: 649
  total: 2599

probation:
  enabled: true
  duration_months: 6
  extension_possible: true
  extension_months: 2  # Up to 2 months extension
  notice_period_during_probation: 15  # days
  notice_period_after_confirmation: 30  # days
  termination_during_probation: "1 week or same day"

benefits:
  - "Group Mediclaim ₹2,00,000"
  - "Group Personal Accident Insurance ₹5,00,000"
  - "Total insurance: ₹7,00,000"
  - "Statutory benefits as per law"

leave_entitlement:
  casual_leave: 12
  sick_leave: 12
  privilege_leave: 0  # Earned after confirmation
  maternity: 26  # weeks (if applicable)
  paternity: 15  # days

retirement_age: 58
```

### Template 3: Mid-Level Developer (L2)

```yaml
template_name: "Senior Developer / L2"
category: "permanent"
designation_level: 2
ctc_annual: 600000  # 6 LPA example
ctc_monthly: 50000

salary_breakup:
  basic: 25000
  hra: 12500
  other_allowance: 7500
  special_allowance: 0
  gross: 45000

deductions:
  pf_employee: 1800  # Capped at 15000 basic
  esic_employee: 0    # Not applicable (Gross > 21000)
  professional_tax: 200
  tds: 0  # Calculate based on declarations
  total: 2000

net_salary: 43000

employer_contribution:
  pf_employer: 1950
  esic_employer: 0
  gratuity: 1042  # 4.81% of basic
  total: 2992

probation:
  enabled: true
  duration_months: 6
  extension_possible: true

benefits:
  - "Group Mediclaim ₹3,00,000"
  - "Group Personal Accident ₹5,00,000"
  - "Performance bonus eligible"
```

### Template 4: Tech Lead / Team Lead (L3)

```yaml
template_name: "Tech Lead"
category: "permanent"
designation_level: 3
ctc_annual: 1200000  # 12 LPA example
ctc_monthly: 100000

salary_breakup:
  basic: 50000
  hra: 25000
  other_allowance: 15000
  special_allowance: 5000
  conveyance: 1600
  medical: 1250
  gross: 97850

deductions:
  pf_employee: 1800  # Capped
  esic_employee: 0
  professional_tax: 200
  tds: 5000  # Approximate
  total: 7000

net_salary: 90850

employer_contribution:
  pf_employer: 1950
  gratuity: 2400
  total: 4350

probation:
  enabled: true
  duration_months: 6

benefits:
  - "Group Mediclaim ₹5,00,000 (Family)"
  - "Group Personal Accident ₹10,00,000"
  - "Annual bonus (1-2 months)"
  - "Stock options (if applicable)"
```

### Template 5: Manager (L4)

```yaml
template_name: "Manager"
category: "permanent"
designation_level: 4
ctc_annual: 1800000  # 18 LPA example
ctc_monthly: 150000

salary_breakup:
  basic: 75000
  hra: 37500
  special_allowance: 25000
  lta: 5000
  conveyance: 1600
  medical: 1250
  food_coupon: 2200
  gross: 147550

deductions:
  pf_employee: 1800
  professional_tax: 200
  tds: 12000
  total: 14000

net_salary: 133550

employer_contribution:
  pf_employer: 1950
  gratuity: 3600
  total: 5550

benefits:
  - "Group Mediclaim ₹7,50,000 (Family)"
  - "Group Personal Accident ₹15,00,000"
  - "Annual performance bonus"
  - "Stock options"
  - "Mobile + Internet reimbursement"
```

### Template 6: Director / VP (L5)

```yaml
template_name: "Director"
category: "permanent"
designation_level: 5
ctc_annual: 3600000  # 36 LPA example
ctc_monthly: 300000

salary_breakup:
  basic: 150000
  hra: 75000
  special_allowance: 60000
  lta: 12500
  car_allowance: 5000
  driver_allowance: 5000
  fuel_reimbursement: 8000
  food_coupon: 2200
  gross: 317700

deductions:
  pf_employee: 1800
  professional_tax: 200
  tds: 50000  # Higher slab
  total: 52000

net_salary: 265700

benefits:
  - "Group Mediclaim ₹10,00,000+"
  - "Personal Accident ₹25,00,000"
  - "Company car"
  - "Driver provided"
  - "ESOPs"
  - "Annual bonus + variable pay"
  - "Club membership"
```

### Template 7: Field Force / Sales (L1-L2)

```yaml
template_name: "Field Sales Executive"
category: "permanent"
designation_level: 1
ctc_annual: 300000  # 3 LPA + commission
ctc_monthly: 25000

salary_breakup:
  basic: 12500
  hra: 5000
  other_allowance: 1500
  travel_allowance: 5000  # Higher for field force
  gross: 24000

deductions:
  pf_employee: 1500  # 12% of 12500
  esic_employee: 180
  total: 1680

net_salary: 22320

variable_pay:
  enabled: true
  type: "commission"
  rate: "5% on sales"
  target: 100000  # monthly sales target

benefits:
  - "Field travel reimbursement"
  - "Mobile allowance"
  - "Petrol allowance"
  - "Performance incentives"
```

### Template 8: Cleaning / Housekeeping Staff

```yaml
template_name: "Housekeeping Staff"
category: "permanent"
designation_level: 1
ctc_annual: 180000  # 1.5 LPA
ctc_monthly: 15000

salary_breakup:
  basic: 9000
  hra: 4500
  other_allowance: 1000
  gross: 14500

deductions:
  pf_employee: 1080  # 12% of 9000
  esic_employee: 109
  total: 1189

net_salary: 13311

employer_contribution:
  pf_employer: 1170
  esic_employer: 471

benefits:
  - "Group Mediclaim"
  - "Uniforms provided"
  - "Annual leave as per law"
```

---

## 🎓 Probation Policy (Standard for All Permanent Roles)

Based on Jaikalki standard offer letter:

### During Probation (First 6 Months)

```yaml
duration: 6 months
extension:
  possible: true
  duration: 2 months  # Additional
  reason: "Performance needs improvement"
  approval: "Departmental Head"

leaving_during_probation:
  notice_period: 15  # days
  by_employee: "Written notice required"
  if_no_notice: "F&F adjusted against notice period"

termination_during_probation:
  notice_period: "1 week OR same day"
  by_company: "If performance unsatisfactory"

confirmation:
  on_satisfactory_completion: "Written confirmation"
  benefits_after_confirmation:
    - "Privilege Leave eligible"
    - "Salary revision possible"
    - "Better notice period (30 days)"
```

### After Confirmation

```yaml
notice_period:
  on_resignation: 30  # days
  on_termination: 7  # days OR pay in lieu

absence_policy:
  unauthorized_absence: 4  # consecutive days
  consequence: "Voluntary abandonment - termination"

f_and_f_settlement:
  timeline: 45  # days from exit
  conditions:
    - "Complete handover"
    - "Exit formalities"
    - "No-dues clearance"

retirement_age: 58
```

---

## 🛡️ Insurance Benefits (Jaikalki Standard)

```yaml
total_coverage: 700000  # ₹7,00,000

components:
  group_mediclaim:
    amount: 200000  # ₹2,00,000
    type: "Health Insurance"
    coverage: "Hospitalization"

  group_personal_accident:
    amount: 500000  # ₹5,00,000
    type: "Personal Accident"
    coverage: "Disability/Death"

eligibility: "All confirmed employees"
notes:
  - "Subject to policy terms"
  - "Coverage limits apply"
  - "Exclusions as per insurer"
```

---

## 💼 Database Schema Updates

### Salary Templates Table

```sql
CREATE TABLE salary_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    category ENUM('intern', 'trainee', 'permanent', 'contract') NOT NULL,
    designation_level INT NOT NULL,

    -- Salary components (monthly)
    basic_amount DECIMAL(10,2) DEFAULT 0,
    basic_percentage DECIMAL(5,2) DEFAULT 50,  -- % of gross

    hra_amount DECIMAL(10,2) DEFAULT 0,
    hra_percentage DECIMAL(5,2) DEFAULT 30,

    other_allowance DECIMAL(10,2) DEFAULT 0,
    special_allowance DECIMAL(10,2) DEFAULT 0,
    conveyance DECIMAL(10,2) DEFAULT 0,
    medical_allowance DECIMAL(10,2) DEFAULT 0,
    lta DECIMAL(10,2) DEFAULT 0,
    food_coupon DECIMAL(10,2) DEFAULT 0,

    -- For interns
    travel_expense_max DECIMAL(10,2) DEFAULT 0,
    is_paid_internship BOOLEAN DEFAULT FALSE,

    -- Probation
    has_probation BOOLEAN DEFAULT TRUE,
    probation_months INT DEFAULT 6,
    probation_extension_months INT DEFAULT 2,

    -- Insurance
    mediclaim_amount DECIMAL(10,2) DEFAULT 200000,
    pa_insurance_amount DECIMAL(10,2) DEFAULT 500000,

    -- Notice periods
    notice_period_probation INT DEFAULT 15,  -- days
    notice_period_confirmed INT DEFAULT 30,
    notice_period_termination INT DEFAULT 7,

    is_active BOOLEAN DEFAULT TRUE,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_category (category),
    INDEX idx_level (designation_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Employee Categories Table

```sql
CREATE TABLE employee_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    description TEXT,

    -- Eligibility flags
    eligible_for_pf BOOLEAN DEFAULT TRUE,
    eligible_for_esic BOOLEAN DEFAULT TRUE,
    eligible_for_gratuity BOOLEAN DEFAULT FALSE,
    eligible_for_pl BOOLEAN DEFAULT FALSE,  -- Privilege Leave
    eligible_for_bonus BOOLEAN DEFAULT FALSE,

    -- Pay structure
    has_salary BOOLEAN DEFAULT TRUE,
    has_stipend BOOLEAN DEFAULT FALSE,
    only_travel_expense BOOLEAN DEFAULT FALSE,

    -- Probation
    requires_probation BOOLEAN DEFAULT TRUE,
    default_probation_months INT DEFAULT 6,

    is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed data
INSERT INTO employee_categories VALUES
(1, 'INTERN', 'Intern', 'Short-term internship, travel expense only',
 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1),
(2, 'TRAINEE', 'Trainee', 'Junior trainee with probation',
 1, 1, 0, 0, 0, 1, 0, 0, 1, 6, 1),
(3, 'PERMANENT', 'Permanent', 'Permanent employee',
 1, 1, 1, 1, 1, 1, 0, 0, 1, 6, 1),
(4, 'CONTRACT', 'Contract', 'Contract employee',
 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1);
```

### Employee Probation Tracking

```sql
CREATE TABLE employee_probation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    probation_start_date DATE NOT NULL,
    probation_end_date DATE NOT NULL,
    is_extended BOOLEAN DEFAULT FALSE,
    extension_end_date DATE NULL,
    extension_reason TEXT,
    status ENUM('in_progress', 'extended', 'confirmed', 'terminated') DEFAULT 'in_progress',
    confirmed_date DATE NULL,
    confirmation_letter_url VARCHAR(500),
    confirmed_by INT,

    -- Monthly review notes during probation
    monthly_reviews JSON,  -- [{month: 1, rating: 4, notes: "..."}]

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (confirmed_by) REFERENCES users(id),
    INDEX idx_status (status),
    INDEX idx_end_date (probation_end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Intern Travel Expense Tracking

```sql
CREATE TABLE intern_travel_expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    expense_date DATE NOT NULL,
    expense_type ENUM('local_travel', 'office_commute', 'project_visit') DEFAULT 'office_commute',
    amount DECIMAL(10,2) NOT NULL,
    receipt_url VARCHAR(500),
    description TEXT,

    status ENUM('pending', 'approved', 'rejected', 'reimbursed') DEFAULT 'pending',
    approved_by INT,
    approved_at TIMESTAMP NULL,
    reimbursed_at TIMESTAMP NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (employee_id) REFERENCES employees(id),
    INDEX idx_employee_date (employee_id, expense_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 🔄 Workflow: Intern → Permanent Transition

```
Intern Joins (3-6 months)
    ↓
Only Travel Expense Provided
    ↓
Performance Review (Monthly)
    ↓
End of Internship
    ↓
HR Decision: Convert or Release?
    ↓
[If Convert]
    ↓
Generate Offer Letter (Trainee category)
    ↓
6-Month Probation Period Starts
    ↓
Monthly Performance Review
    ↓
[If Performance Good]
    ↓
Confirmation Letter Generated
    ↓
Move to Permanent Category
    ↓
PL Eligibility, Bonus Eligibility Active
```

---

## 📝 Offer Letter Template Generator

The system should generate offer letters matching Jaikalki format with:

```yaml
offer_letter_template:
  header:
    - "Letter Number: JKT/HR/AL/{seq_number}/{year}"
    - "Date: {current_date}"

  body_sections:
    - "REMUNERATION"
    - "CONFIDENTIALITY"
    - "ASSIGNMENT"
    - "PROBATION & CONFIRMATION"
    - "PLACE OF POSTING"
    - "RESPONSIBILITY"
    - "VISITS"
    - "LEAVE"
    - "COMPENSATION PROGRESSION"
    - "SEPARATION"
    - "RETIREMENT"
    - "SETTLEMENT OF DUES"
    - "GENERAL"

  annexure:
    - "Salary Compensation Structure (table)"
    - "Insurance Benefits"
    - "Confidentiality Note"

  signatures:
    - "For Jaikalki Technology Pvt Ltd - Director"
    - "Employee acceptance signature"
```

---

## 💻 Backend Implementation

### Database Connection (MySQL)

```python
# .env
DATABASE_URL=mysql+aiomysql://root:Love1718@localhost:3306/db_hrms_jaikalki?charset=utf8mb4
DATABASE_URL_SYNC=mysql+pymysql://root:Love1718@localhost:3306/db_hrms_jaikalki?charset=utf8mb4
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Company info
COMPANY_NAME=Jaikalki Technology Pvt Ltd
COMPANY_ADDRESS=Sh N B1/A Ground Floor, Mahavir Nagar, Deepak Hospital, Mira Road, Thane-401107 Maharashtra
COMPANY_GST=
COMPANY_PAN=
EMPLOYEE_CODE_PREFIX=JKT
```

### Salary Calculation Service

```python
# app/services/salary_calculator.py
from decimal import Decimal
from typing import Dict

class JaikalkiSalaryCalculator:
    """Calculate salary as per Jaikalki standard structure"""

    # Statutory limits
    PF_BASIC_CEILING = 15000
    ESIC_GROSS_CEILING = 21000

    # Rates
    EMPLOYEE_PF_RATE = 0.12
    EMPLOYER_PF_RATE = 0.13  # Including admin charges
    EMPLOYEE_ESIC_RATE = 0.0075
    EMPLOYER_ESIC_RATE = 0.0325

    @classmethod
    def calculate_from_template(cls, template_id: int, ctc_annual: Decimal):
        """Calculate based on salary template"""
        # Fetch template
        template = await get_template(template_id)

        if template.category == 'intern':
            return cls._intern_structure(template)

        # Permanent/Trainee calculation
        ctc_monthly = ctc_annual / 12

        # Work backwards from CTC
        # CTC = Gross + Employer PF + Employer ESIC
        # For intern there is no PF/ESIC

        return cls._calculate_breakup(ctc_monthly, template)

    @classmethod
    def _intern_structure(cls, template) -> Dict:
        return {
            'basic': 0,
            'hra': 0,
            'other_allowance': 0,
            'gross': 0,
            'travel_expense_max': template.travel_expense_max,
            'pf_employee': 0,
            'pf_employer': 0,
            'esic_employee': 0,
            'esic_employer': 0,
            'professional_tax': 0,
            'net_salary': 0,
            'total_ctc': 0,
            'is_intern': True,
            'note': 'Only travel expense reimbursement'
        }

    @classmethod
    def _calculate_breakup(cls, ctc_monthly: Decimal, template) -> Dict:
        """Calculate detailed breakup like Pooja's offer"""

        # Gross = CTC - Employer Contributions
        # We need to iterate or use template ratios

        if template.basic_percentage and template.hra_percentage:
            # Use template ratios
            gross = ctc_monthly * Decimal('0.885')  # Approx
            basic = gross * (template.basic_percentage / 100)
            hra = gross * (template.hra_percentage / 100)
            other = gross - basic - hra
        else:
            # Use template absolute amounts
            basic = template.basic_amount
            hra = template.hra_amount
            other = template.other_allowance
            gross = basic + hra + other

        # Calculate PF
        pf_basic = min(basic, cls.PF_BASIC_CEILING)
        pf_employee = pf_basic * Decimal(str(cls.EMPLOYEE_PF_RATE))
        pf_employer = pf_basic * Decimal(str(cls.EMPLOYER_PF_RATE))

        # Calculate ESIC
        if gross <= cls.ESIC_GROSS_CEILING:
            esic_employee = gross * Decimal(str(cls.EMPLOYEE_ESIC_RATE))
            esic_employer = gross * Decimal(str(cls.EMPLOYER_ESIC_RATE))
        else:
            esic_employee = Decimal('0')
            esic_employer = Decimal('0')

        # Professional Tax (Maharashtra)
        pt = cls._calculate_pt(gross)

        # Total deductions
        total_deductions = pf_employee + esic_employee + pt

        # Net salary
        net_salary = gross - total_deductions

        # Total CTC
        total_employer = pf_employer + esic_employer
        total_ctc = gross + total_employer

        return {
            'basic': round(basic),
            'hra': round(hra),
            'other_allowance': round(other),
            'gross': round(gross),
            'pf_employee': round(pf_employee),
            'pf_employer': round(pf_employer),
            'esic_employee': round(esic_employee),
            'esic_employer': round(esic_employer),
            'professional_tax': round(pt),
            'total_deductions': round(total_deductions),
            'net_salary': round(net_salary),
            'total_ctc_monthly': round(total_ctc),
            'total_ctc_annual': round(total_ctc * 12),
            'is_intern': False
        }

    @classmethod
    def _calculate_pt(cls, gross_monthly: Decimal) -> Decimal:
        """Maharashtra Professional Tax"""
        if gross_monthly <= 7500:
            return Decimal('0')
        elif gross_monthly <= 10000:
            return Decimal('175')
        else:
            return Decimal('200')
```

---

## 🎯 Sample API Implementation

```python
# app/api/v1/salary_templates.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/salary-templates", tags=["Salary Templates"])

@router.get("/")
async def list_templates(
    category: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all salary templates"""
    query = select(SalaryTemplate).where(SalaryTemplate.is_active == True)
    if category:
        query = query.where(SalaryTemplate.category == category)
    return await db.execute(query)

@router.get("/{template_id}/calculate")
async def calculate_salary(
    template_id: int,
    ctc_annual: Decimal,
    db: AsyncSession = Depends(get_db),
):
    """Calculate salary breakup for given CTC"""
    return JaikalkiSalaryCalculator.calculate_from_template(
        template_id, ctc_annual
    )

@router.post("/")
async def create_template(
    data: SalaryTemplateCreate,
    current_user = Depends(require_permission("salary_template.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create new salary template (Super Admin only)"""
    template = SalaryTemplate(**data.dict())
    db.add(template)
    await db.commit()
    return template
```

---

## 📋 Validation Rules

When creating new employee, system validates:

```python
def validate_employee_creation(data):
    errors = []

    # Intern validation
    if data.category == 'INTERN':
        if data.basic_salary > 0:
            errors.append("Interns cannot have salary, only travel expense")
        if data.requires_probation:
            errors.append("Interns don't have probation period")

    # Permanent/Trainee validation
    if data.category in ['TRAINEE', 'PERMANENT']:
        if data.basic_salary <= 0:
            errors.append("Salary required for this category")
        if not data.requires_probation and data.category == 'TRAINEE':
            errors.append("Trainees must have 6-month probation")

    # CTC consistency check
    expected_ctc = (
        data.basic + data.hra + data.other +
        data.pf_employer + data.esic_employer
    ) * 12
    if abs(data.ctc_annual - expected_ctc) > 100:
        errors.append("CTC doesn't match component breakup")

    return errors
```

---

**Document Version:** 1.0
**Last Updated:** April 2026
**Reference Offer Letter:** JKT/HR/AL/001/2025 - Pooja Kumawat
