"""PF ECR format — pinned against a file the EPFO portal accepted.

ACCEPTED_AUGUST_2026 is the August 2026 ECR that was uploaded and
accepted (built by hand with the ₹15,000 ceiling). Regenerating it from
equivalent payslip values must reproduce it byte for byte, and the
validator must find no errors.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from app.services.payroll_service import (
    build_pf_ecr,
    ecr_rows,
    ecr_text,
    validate_ecr_rows,
)

ACCEPTED_AUGUST_2026 = (
    "101111406024#~#SHYAMVEER SINGH#~#77000#~#15000#~#15000#~#15000#~#1800#~#1250#~#550#~#0#~#0\n"
    "102242721449#~#ROHITKUMAR KANNOJIYA#~#77000#~#15000#~#15000#~#15000#~#1800#~#1250#~#550#~#0#~#0\n"
    "100201240446#~#KRUNAL TRIVEDI#~#77000#~#15000#~#15000#~#15000#~#1800#~#1250#~#550#~#0#~#0\n"
    "101815844075#~#JINCY MATHEW#~#21084#~#11275#~#11275#~#11275#~#1353#~#939#~#414#~#0#~#0\n"
    "102242730233#~#SANJAY JAISWAR#~#19868#~#11275#~#11275#~#11275#~#1353#~#939#~#414#~#2#~#0\n"
    "101577987606#~#VIKAS KOTIYAN#~#21084#~#11275#~#11275#~#11275#~#1353#~#939#~#414#~#0#~#0\n"
    "102317640610#~#SOHAM ROY#~#11687#~#6250#~#6250#~#6250#~#750#~#521#~#229#~#0#~#0\n"
    "102250493103#~#POOJA KUMAWAT#~#21083#~#11274#~#11274#~#11274#~#1353#~#939#~#414#~#0#~#0\n"
    "102291980472#~#ATHARV SACHIN PARTE#~#15223#~#8466#~#8466#~#8466#~#1016#~#705#~#311#~#1#~#0\n"
)


def _fixture():
    """Employees + payslips carrying the stored values behind the file."""
    employees, payslips = {}, []
    for i, line in enumerate(ACCEPTED_AUGUST_2026.strip().splitlines(), start=1):
        f = line.split("#~#")
        first, _, last = f[1].title().rpartition(" ")
        employees[i] = SimpleNamespace(
            id=i, employee_code=f"JKT{i:03d}", uan_number=f[0],
            first_name=first, last_name=last, eps_member=True,
        )
        payslips.append(SimpleNamespace(
            employee_id=i,
            gross=Decimal(f[2]),
            pf_wages=Decimal(f[3]),
            eps_wages=Decimal(f[4]),
            edli_wages=Decimal(f[5]),
            pf_employee=Decimal(f[6]),
            days_lop=Decimal(f[9]),
            basic=Decimal(f[3]),
            days_paid=Decimal(30),
            working_days=Decimal(31),
        ))
    return employees, payslips


def test_regenerates_accepted_august_file_exactly() -> None:
    employees, payslips = _fixture()
    assert build_pf_ecr(None, payslips, employees) == ACCEPTED_AUGUST_2026


def test_no_header_or_comment_lines() -> None:
    employees, payslips = _fixture()
    text = build_pf_ecr(None, payslips, employees)
    assert not any(line.startswith("#") for line in text.splitlines())
    assert all(len(line.split("#~#")) == 11 for line in text.splitlines())


def test_accepted_file_passes_validation() -> None:
    employees, payslips = _fixture()
    rows, excluded = ecr_rows(payslips, employees)
    issues = validate_ecr_rows(
        rows, pf_cap=Decimal(15000), eps_cap=Decimal(15000),
        edli_cap=Decimal(15000), days_in_month=31,
    )
    assert excluded == []
    assert [i for i in issues if i["level"] == "error"] == []


def test_new_ceiling_september_row() -> None:
    """₹25,000 from 17 Sep, pro-rata: Sept EPF wages 19,667, EPS and
    EDLI stay at ₹15,000, col 9 = 2,360 − 1,250."""
    employees, _ = _fixture()
    slip = SimpleNamespace(
        employee_id=1, gross=Decimal(77000), pf_wages=Decimal(19667),
        eps_wages=Decimal(15000), edli_wages=Decimal(15000),
        pf_employee=Decimal(2360), days_lop=Decimal(0), basic=Decimal(39475),
        days_paid=Decimal(30), working_days=Decimal(30),
    )
    rows, _ = ecr_rows([slip], {1: employees[1]})
    assert ecr_text(rows) == (
        "101111406024#~#SHYAMVEER SINGH#~#77000#~#19667#~#15000#~#15000"
        "#~#2360#~#1250#~#1110#~#0#~#0\n"
    )
    issues = validate_ecr_rows(
        rows, pf_cap=Decimal("19666.67"), eps_cap=Decimal(15000),
        edli_cap=Decimal(15000), days_in_month=30,
    )
    assert [i for i in issues if i["level"] == "error"] == []


def test_non_eps_member_puts_full_share_in_col9() -> None:
    employees, _ = _fixture()
    slip = SimpleNamespace(
        employee_id=1, gross=Decimal(77000), pf_wages=Decimal(15000),
        eps_wages=Decimal(0), edli_wages=Decimal(15000),
        pf_employee=Decimal(1800), days_lop=Decimal(0), basic=Decimal(39475),
        days_paid=Decimal(30), working_days=Decimal(30),
    )
    rows, _ = ecr_rows([slip], {1: employees[1]})
    r = rows[0]
    assert (r["eps_wages"], r["eps_contri"], r["epf_eps_diff"]) == (0, 0, 1800)


def test_validator_catches_old_generator_mistakes() -> None:
    employees, payslips = _fixture()
    rows, _ = ecr_rows(payslips[:1], employees)
    bad = dict(rows[0], epf_eps_diff=700, edli_wages=19667, epf_wages=19667)
    issues = validate_ecr_rows(
        [bad], pf_cap=Decimal(15000), eps_cap=Decimal(15000),
        edli_cap=Decimal(15000), days_in_month=31,
    )
    msgs = " | ".join(i["message"] for i in issues if i["level"] == "error")
    assert "EPF-EPS difference" in msgs
    assert "EDLI wages exceed the EDLI ceiling" in msgs


def test_missing_uan_is_reported_not_written() -> None:
    employees, payslips = _fixture()
    employees[1].uan_number = ""
    rows, excluded = ecr_rows(payslips, employees)
    assert len(rows) == 8
    assert excluded[0]["reason"] == "No UAN on record"
