"""Jaikalki HRMS salary calculator.

Mirrors `hrms_structure/SALARY_STRUCTURE_JAIKALKI.md` exactly. Test contract:

    Trainee L1 (template JKT-TRAINEE-L1, CTC 270588) →
        basic 15000, hra 4500, other 450, gross 19950
        pf_emp 1800, esic_emp 150, pt 0  → net 18000
        pf_employer 1950, esic_employer 649 → ctc_monthly 22549
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.models import Employee, SalaryTemplate

# ── Statutory caps & rates ─────────────────────────────────────────────
PF_BASIC_CAP = Decimal("15000")
PF_EMPLOYEE_RATE = Decimal("0.12")
PF_EMPLOYER_RATE = Decimal("0.13")           # Jaikalki uses 13% (incl. admin charges)

ESIC_GROSS_THRESHOLD = Decimal("21000")
ESIC_EMPLOYEE_RATE = Decimal("0.0075")
ESIC_EMPLOYER_RATE = Decimal("0.0325")


def _pt_slab(state: Optional[str], gender: Optional[str], gross: Decimal) -> Decimal:
    """Maharashtra-only Professional Tax slab.

    Jaikalki operates out of Mira Road, Thane, so only the MH schedule
    is encoded. Anything else (or no state set) returns 0 — opt-in by
    setting `pt_state` to MH on the employee record.

    Women earning ≤ ₹25,000/m are exempt; everyone else uses the
    standard slab. Feb's ₹300 top-up is left to payroll.
    """
    if not state:
        return Decimal(0)
    code = state.strip().upper()
    if code not in {"MH", "MAHARASHTRA"}:
        return Decimal(0)

    g = (gender or "").strip().lower()
    if g in {"female", "f", "woman"} and gross <= Decimal("25000"):
        return Decimal(0)
    if gross <= Decimal("7500"):
        return Decimal(0)
    if gross <= Decimal("10000"):
        return Decimal(175)
    return Decimal(200)


def _round(value: Decimal) -> int:
    """ROUND_HALF_UP money rounding so 648.375 → 649 (matches Pooja's offer)."""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@dataclass
class SalaryBreakup:
    template_code: str
    template_name: str
    category: str
    is_intern: bool

    basic: int = 0
    hra: int = 0
    other_allowance: int = 0
    special_allowance: int = 0
    conveyance: int = 0
    medical_allowance: int = 0
    lta: int = 0
    food_coupon: int = 0

    gross: int = 0

    pf_employee: int = 0
    esic_employee: int = 0
    professional_tax: int = 0
    total_deductions: int = 0

    net_salary: int = 0

    pf_employer: int = 0
    esic_employer: int = 0

    total_ctc_monthly: int = 0
    total_ctc_annual: int = 0

    # Intern-specific
    travel_expense_max: int = 0
    is_paid_internship: bool = False

    # Misc helpful info for UI
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "template_code": self.template_code,
            "template_name": self.template_name,
            "category": self.category,
            "is_intern": self.is_intern,
            "basic": self.basic,
            "hra": self.hra,
            "other_allowance": self.other_allowance,
            "special_allowance": self.special_allowance,
            "conveyance": self.conveyance,
            "medical_allowance": self.medical_allowance,
            "lta": self.lta,
            "food_coupon": self.food_coupon,
            "gross": self.gross,
            "pf_employee": self.pf_employee,
            "esic_employee": self.esic_employee,
            "professional_tax": self.professional_tax,
            "total_deductions": self.total_deductions,
            "net_salary": self.net_salary,
            "pf_employer": self.pf_employer,
            "esic_employer": self.esic_employer,
            "total_ctc_monthly": self.total_ctc_monthly,
            "total_ctc_annual": self.total_ctc_annual,
            "travel_expense_max": self.travel_expense_max,
            "is_paid_internship": self.is_paid_internship,
            "notes": self.notes,
        }


class JaikalkiSalaryCalculator:
    """Resolve a `SalaryTemplate` (+ optional CTC override) to a breakup."""

    def calculate(
        self,
        template: SalaryTemplate,
        ctc_annual: Optional[Decimal | int | float] = None,
        employee: Optional[Employee] = None,
    ) -> SalaryBreakup:
        if template.category == "intern":
            return self._intern(template)
        return self._standard(template, ctc_annual, employee)

    # ── intern ────────────────────────────────────────────────────────
    def _intern(self, t: SalaryTemplate) -> SalaryBreakup:
        return SalaryBreakup(
            template_code=t.template_code,
            template_name=t.template_name,
            category=t.category,
            is_intern=True,
            travel_expense_max=_round(Decimal(t.travel_expense_max or 0)),
            is_paid_internship=bool(t.is_paid_internship),
            notes=[
                "Interns receive only travel expense reimbursement.",
                "No salary, PF, or ESIC during the internship.",
            ],
        )

    # ── standard (trainee / permanent / contract) ─────────────────────
    def _standard(
        self,
        t: SalaryTemplate,
        ctc_annual: Optional[Decimal | int | float],
        emp: Optional[Employee] = None,
    ) -> SalaryBreakup:
        # Resolve per-employee statutory overrides up-front. When no
        # employee is given (template-only preview) the defaults match
        # legacy behaviour exactly.
        pf_opt_out = bool(getattr(emp, "pf_opt_out", False))
        pf_basic_cap = (
            Decimal(getattr(emp, "pf_basic_cap_override", None) or PF_BASIC_CAP)
        )
        esic_force_exempt = bool(getattr(emp, "esic_force_exempt", False))
        pt_state = getattr(emp, "pt_state", None)
        gender = getattr(emp, "gender", None)
        # Use the template's explicit components (Pooja's case).
        basic = Decimal(t.basic_amount or 0)
        hra = Decimal(t.hra_amount or 0)
        other = Decimal(t.other_allowance or 0)
        special = Decimal(t.special_allowance or 0)
        conveyance = Decimal(t.conveyance or 0)
        medical = Decimal(t.medical_allowance or 0)
        lta = Decimal(t.lta or 0)
        food = Decimal(t.food_coupon or 0)

        # Hybrid back-fill: when basic+HRA aren't hard-coded on the
        # template (the typical "structure-only" template), derive them
        # from the employee's CTC. The fixed allowances on the template
        # (other / special / medical / etc.) layer on top so the gross =
        # ratio-derived(basic+hra) + fixed extras.
        #
        # We fire whenever both basic_amount and hra_amount are zero —
        # not also other_allowance — because mixing fixed-rupee adders
        # with ratio-driven basic/HRA is the common case (a small
        # special allowance or medical adder while basic still scales
        # with CTC).
        if ctc_annual and basic == 0 and hra == 0:
            ctc_monthly = Decimal(ctc_annual) / Decimal(12)
            # Prefer the template's own percentages (default 50% basic,
            # 30% HRA-of-basic per the model defaults). Fall back to the
            # legacy Jaikalki ratios if both are zero on the template.
            basic_pct = Decimal(t.basic_percentage or 0) / Decimal(100)
            hra_pct = Decimal(t.hra_percentage or 0) / Decimal(100)
            if basic_pct > 0:
                basic = (ctc_monthly * basic_pct).quantize(Decimal("1"))
                hra = (basic * hra_pct).quantize(Decimal("1"))
            else:
                # Legacy Jaikalki ratios from the gross side.
                gross_est = ctc_monthly / Decimal("1.13")
                basic = (gross_est * Decimal("0.6678")).quantize(Decimal("1"))
                hra = (gross_est * Decimal("0.2256")).quantize(Decimal("1"))
                # Only overwrite `other` when the template didn't pin a
                # fixed value — preserves the user's intent.
                if other == 0:
                    other = (gross_est * Decimal("0.0226")).quantize(Decimal("1"))

            # Pad `special_allowance` so the resulting CTC matches the
            # employee's configured ctc_annual exactly. Iterate up to
            # six times so the employer-side ESIC threshold can flip
            # mid-convergence without leaving a residual gap. The loop
            # is allowed to shrink `special` too — bumping past the
            # ESIC threshold can over-correct on the first pass.
            initial_special = special
            for _ in range(6):
                gross_try = (
                    basic + hra + other + special + conveyance
                    + medical + lta + food
                )
                if pf_opt_out:
                    pf_er_try = Decimal(0)
                else:
                    pf_basic_try = min(basic, pf_basic_cap)
                    pf_er_try = pf_basic_try * PF_EMPLOYER_RATE
                if (
                    not esic_force_exempt
                    and gross_try <= ESIC_GROSS_THRESHOLD
                ):
                    esic_er_try = gross_try * ESIC_EMPLOYER_RATE
                else:
                    esic_er_try = Decimal(0)
                ctc_try = gross_try + pf_er_try + esic_er_try
                gap = ctc_monthly - ctc_try
                if abs(gap) < Decimal("1"):
                    break
                # Adjust special by the gap. Don't shrink below the
                # template's own initial special_allowance — the template
                # author put it there for a reason.
                new_special = (special + gap).quantize(Decimal("1"))
                if new_special < initial_special:
                    special = initial_special
                    break
                special = new_special

        gross = basic + hra + other + special + conveyance + medical + lta + food

        if pf_opt_out:
            pf_employee = Decimal(0)
            pf_employer = Decimal(0)
        else:
            pf_basic = min(basic, pf_basic_cap)
            pf_employee = pf_basic * PF_EMPLOYEE_RATE
            pf_employer = pf_basic * PF_EMPLOYER_RATE

        if not esic_force_exempt and gross <= ESIC_GROSS_THRESHOLD:
            esic_employee = gross * ESIC_EMPLOYEE_RATE
            esic_employer = gross * ESIC_EMPLOYER_RATE
        else:
            esic_employee = Decimal(0)
            esic_employer = Decimal(0)

        # Professional tax: zero unless the employee record names a
        # state. Maharashtra-bound female employees ≤ ₹25k are exempt;
        # other states slot into their published slabs.
        pt = _pt_slab(pt_state, gender, gross)

        # Round each component first, then sum — so the totals match
        # Jaikalki's offer letter to the rupee (22549 not 22548).
        gross_i = _round(gross)
        pf_emp_i = _round(pf_employee)
        esic_emp_i = _round(esic_employee)
        pf_er_i = _round(pf_employer)
        esic_er_i = _round(esic_employer)
        pt_i = _round(pt)

        total_deductions_i = pf_emp_i + esic_emp_i + pt_i
        net_i = gross_i - total_deductions_i
        ctc_monthly_i = gross_i + pf_er_i + esic_er_i

        return SalaryBreakup(
            template_code=t.template_code,
            template_name=t.template_name,
            category=t.category,
            is_intern=False,
            basic=_round(basic),
            hra=_round(hra),
            other_allowance=_round(other),
            special_allowance=_round(special),
            conveyance=_round(conveyance),
            medical_allowance=_round(medical),
            lta=_round(lta),
            food_coupon=_round(food),
            gross=gross_i,
            pf_employee=pf_emp_i,
            esic_employee=esic_emp_i,
            professional_tax=pt_i,
            total_deductions=total_deductions_i,
            net_salary=net_i,
            pf_employer=pf_er_i,
            esic_employer=esic_er_i,
            total_ctc_monthly=ctc_monthly_i,
            total_ctc_annual=ctc_monthly_i * 12,
        )
