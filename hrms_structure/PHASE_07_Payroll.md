# Phase 7: Payroll & Compliance - Jaikalki HRMS

**Duration:** 10-14 days
**Hours:** 90
**Priority:** HIGH
**Depends on:** Phase 6

---

## Objective

Build complete payroll engine with Indian compliance (PF, ESI, TDS, PT), payslip generation, reimbursement workflows, and **Jaikalki-specific offer letter generation**.

## Reference Documents

- HRMS_Architecture.md → Section 8.4 (Payroll)
- **SALARY_STRUCTURE_JAIKALKI.md** (entire file) - For exact calculations
- Sample offer letter: Pooja Kumawat (JKT014)

## Deliverables

- ✅ Salary structure management (Jaikalki templates)
- ✅ Automated payroll processing
- ✅ Payslip PDF generation (Jaikalki branded)
- ✅ PF (12% employee, 13% employer) calculation
- ✅ ESI (0.75% / 3.25%) calculation
- ✅ TDS calculation (slab-based)
- ✅ Professional Tax (Maharashtra)
- ✅ Reimbursement workflow
- ✅ Investment declaration (80C, 80D, etc.)
- ✅ Form 16 generation
- ✅ Bank file export (NEFT batch)
- ✅ **Offer letter PDF generation (Jaikalki format)**
- ✅ **Confirmation letter generation (post-probation)**
- ✅ **Intern travel expense reimbursement**

---

## Tasks

### Task 7.1: Database Models (6h)

```python
- SalaryStructure (id, employee_id, ctc, basic, hra,
                   special_allowance, conveyance,
                   medical, lta, effective_from)

- SalaryComponent (id, name, type (earning/deduction),
                   calculation_type (fixed/percentage/formula),
                   formula, applicable_to)

- PayrollRun (id, month, year, status, run_by,
              run_at, total_amount, finalized_at)

- Payslip (id, employee_id, payroll_run_id, gross,
           deductions, net_pay, pf, esi, tds, pt,
           generated_pdf_url, days_paid, days_lop)

- Reimbursement (id, employee_id, category, amount,
                 bill_url, bill_date, status,
                 approver_id, approved_at, paid_in)

- InvestmentDeclaration (id, employee_id, year, section_80c,
                         section_80d, hra_exemption,
                         home_loan_interest, total_savings)

- TaxRegime (id, employee_id, year, regime, locked_at)

- BankFileExport (id, payroll_run_id, file_url,
                  total_amount, total_employees, generated_at)
```

### Task 7.2: Salary Components Seed (3h)

**Earnings:**
- Basic (40-50% of CTC)
- HRA (40% of basic for metro, 50% for non-metro)
- Special Allowance (balancing component)
- Conveyance Allowance
- Medical Allowance
- LTA (Leave Travel Allowance)

**Deductions:**
- PF (12% of basic, capped at ₹1,800)
- ESI (0.75% if gross < ₹21,000)
- Professional Tax (₹200/month - varies by state)
- TDS (computed)
- Loan EMI

### Task 7.3: PF Calculation (4h)

```python
# PF calculation
def calculate_pf(basic):
    pf_eligible_amount = min(basic, 15000)
    employee_pf = pf_eligible_amount * 0.12
    employer_pf = pf_eligible_amount * 0.12
    eps = min(pf_eligible_amount * 0.0833, 1250)
    return {
        'employee_pf': employee_pf,
        'employer_pf': employer_pf - eps,
        'eps': eps,
        'total': employee_pf + employer_pf
    }
```

### Task 7.4: ESI Calculation (3h)

```python
# ESI calculation
def calculate_esi(gross_salary):
    if gross_salary > 21000:
        return {'employee_esi': 0, 'employer_esi': 0}
    return {
        'employee_esi': gross_salary * 0.0075,
        'employer_esi': gross_salary * 0.0325
    }
```

### Task 7.5: TDS Calculation (6h)

**Old Regime Slabs (FY 2025-26):**
- 0 - 2.5L: 0%
- 2.5L - 5L: 5%
- 5L - 10L: 20%
- Above 10L: 30%

**New Regime Slabs (FY 2025-26):**
- 0 - 3L: 0%
- 3L - 6L: 5%
- 6L - 9L: 10%
- 9L - 12L: 15%
- 12L - 15L: 20%
- Above 15L: 30%

Plus:
- Standard Deduction (₹50,000)
- HRA exemption
- Section 80C (₹1.5L)
- Section 80D (medical insurance)
- Cess (4%)
- Surcharge (>50L)

### Task 7.6: Professional Tax (2h)

State-wise PT slabs:
- Maharashtra
- Karnataka
- West Bengal
- Tamil Nadu
- Andhra Pradesh
- Telangana

### Task 7.7: Payroll Engine (8h)

`app/services/payroll_service.py`:
- `calculate_salary(employee, month, year)`
- `apply_lop(employee, days_present, working_days)`
- `process_payroll(month, year)` - bulk
- `finalize_payroll(run_id)` - lock
- `revert_payroll(run_id)` - if not finalized
- `generate_payslip(employee, run_id)` - PDF

### Task 7.8: PDF Generation (5h)

Use `reportlab`:
- Company logo header
- Employee details
- Earnings table
- Deductions table
- Net pay highlighted
- YTD summary
- Watermark
- Digital signature

### Task 7.9: Reimbursement Service (4h)

- Submit claim with bill
- Manager approval
- HR final approval
- Pay in next payroll
- Categories: Travel, Food, Internet, Phone, Medical, Books

### Task 7.10: Investment Declaration (4h)

Annual declaration:
- Section 80C (LIC, PPF, ELSS, etc.)
- Section 80D (Medical insurance)
- HRA (rent receipts)
- Home loan interest
- Educational loan
- Donations (80G)
- Proof upload

### Task 7.11: Form 16 Generation (5h)

Annual Form 16:
- Part A (TDS details)
- Part B (Salary breakup)
- Auto-generate PDF
- Email to employee
- Bulk download for HR

### Task 7.12: Bank File Export (4h)

Generate NEFT/RTGS batch file:
- HDFC Bank format
- ICICI Bank format
- SBI format
- Excel/CSV export
- Validation before export

### Task 7.12.1: Jaikalki Offer Letter Generator (5h)

Generate offer letter PDF matching exact Jaikalki format:

**`app/services/offer_letter_generator.py`:**

```python
class JaikalkiOfferLetterGenerator:
    """Generate offer letter PDF in Jaikalki Technology format"""

    def generate(self, employee_id: int) -> str:
        """Returns S3 URL of generated PDF"""
        employee = await get_employee(employee_id)

        # Use ReportLab or WeasyPrint
        # Match exact format from Pooja's offer letter (JKT014)

        sections = [
            self._header(employee),
            self._address_block(employee),
            self._subject_line(),
            self._greeting(employee),
            self._remuneration_section(employee),
            self._confidentiality_section(),
            self._assignment_section(),
            self._probation_section(),
            self._place_of_posting(employee),
            self._responsibility_section(),
            self._visits_section(),
            self._leave_section(),
            self._compensation_progression(),
            self._separation_section(),
            self._retirement_section(),
            self._settlement_section(),
            self._general_section(),
            self._signature_block(employee),
            self._annexure_a(employee),  # Salary structure table
        ]

        return self._build_pdf(sections, employee)
```

**Offer Letter Number Format:**
```
JKT/HR/AL/{seq_number_padded}/{year}
Example: JKT/HR/AL/014/2025
```

**Offer Letter PDF Structure:**

```
Page 1:
─────────────────────────────────────
JKT/HR/AL/001/2025                    Date: 01st Jan 2026

Ms. Pooja Kumawat,
Emp. Code: JKT014
[Address]

Subject: Appointment Letter

Dear Ms. Pooja,

[Body sections 1-13]

Page 2 - Annexure 'A':
─────────────────────────────────────
Annexure - w.e.f. 01st Jan 2026
Name: Pooja Kumawat
Designation: Front-end Developer - Flutter
Department: IT
Employee Code: JKT014

Salary Compensation Structure:
[Detailed table matching offer]

Insurance Benefits: ₹7,00,000
- Mediclaim: ₹2,00,000
- Personal Accident: ₹5,00,000
```

### Task 7.12.2: Confirmation Letter Generator (3h)

After 6-month probation, generate confirmation letter:

```python
class JaikalkiConfirmationLetterGenerator:
    def generate(self, employee_id: int) -> str:
        # Trigger when probation_end_date reached
        # And HR confirms employee
        # Generate PDF with confirmation details

        sections = [
            self._header(),
            self._congratulations(employee),
            self._effective_date(),
            self._revised_compensation(),  # If salary changed
            self._new_terms(),  # 30-day notice etc.
            self._signature_block()
        ]
```

### Task 7.12.3: Intern Travel Expense Reimbursement (3h)

Special workflow for interns (no regular salary):

```python
class InternReimbursementService:
    """Process intern travel expenses monthly"""

    async def process_monthly_reimbursement(self, month, year):
        # Fetch all approved travel expenses
        # Group by intern
        # Generate reimbursement
        # Add to bank transfer batch
        # Send notification

    async def generate_reimbursement_slip(self, intern_id, month):
        # PDF showing all expenses for the month
        # Total reimbursement amount
        # Bank details
```

### Task 7.13: APIs (6h)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/payroll/payslips/me` | My payslips |
| GET | `/payroll/payslips/{id}/pdf` | Download PDF |
| POST | `/payroll/run` | HR triggers payroll |
| GET | `/payroll/runs` | History |
| POST | `/payroll/runs/{id}/finalize` | Lock |
| POST | `/payroll/reimbursements` | Submit claim |
| GET | `/payroll/reimbursements/me` | My claims |
| GET | `/payroll/reimbursements/pending` | For approval |
| POST | `/payroll/declaration` | Submit declaration |
| GET | `/payroll/declaration/me` | My declaration |
| GET | `/payroll/form16/{year}` | Download Form 16 |
| POST | `/payroll/bank-file/{run_id}` | Generate bank file |
| **POST** | **`/payroll/offer-letter/{employee_id}`** | **Generate offer letter (Jaikalki format)** |
| **POST** | **`/payroll/confirmation-letter/{employee_id}`** | **Generate confirmation letter** |
| **POST** | **`/payroll/intern-reimbursement/process`** | **Process intern travel expenses** |
| **GET** | **`/payroll/intern-reimbursement/{intern_id}/{month}/{year}`** | **Intern reimbursement slip** |

### Task 7.14: Compliance Reports (5h)

- PF return (Form 5/10/12A)
- ESI return
- TDS return (Form 24Q)
- PT challan
- Auto-generate monthly

### Task 7.15: Flutter - Payslip View (5h)

- List of payslips (year-wise)
- Tap to view
- Download PDF
- Share via WhatsApp/Email
- Quick stats

### Task 7.16: Flutter - Reimbursement (6h)

- Submit claim form
- Bill photo upload
- OCR (basic - amount detection)
- Status tracking
- History view
- Approval inbox (manager)

### Task 7.17: Flutter - Investment Declaration (5h)

- Section-wise input
- Tax saving calculator
- Old vs New regime comparison
- Proof upload
- Submit before March 31

### Task 7.18: Tests (5h)

- PF calculation accuracy
- ESI threshold edge cases
- TDS for both regimes
- Multi-state PT
- LOP calculation
- Payroll workflow end-to-end

---

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 8.4 (Payroll).

Implement Phase 7 (Payroll & Compliance) as described in PHASE_07_Payroll.md.

This is critical and India-specific:
- PF (12%, capped at ₹1,800)
- ESI (0.75% if gross < ₹21,000)
- TDS (slab-based, both Old & New regime)
- Professional Tax (state-wise)
- Form 16 annual generation
- Bank file export (NEFT batch)

Build:
1. Salary structure management
2. Payroll processing engine (bulk)
3. Payslip PDF generation with company branding
4. Reimbursement workflow
5. Investment declaration form
6. Form 16 auto-generation
7. Bank file exports for major banks

Mobile:
- Payslip viewer
- Reimbursement submission with bill photos
- Investment declaration with tax calculator

Test compliance calculations thoroughly with edge cases.
```

---

## Next: Phase 8 - Justice Portal
