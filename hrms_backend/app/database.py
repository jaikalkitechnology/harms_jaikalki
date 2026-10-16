from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_tables() -> None:
    """Create any tables that don't yet exist.

    For dev / first-boot convenience. Production should use Alembic
    migrations (`alembic upgrade head`) instead — this is enabled by
    `settings.AUTO_CREATE_TABLES`. `create_all()` only adds missing
    tables, it does NOT migrate columns/indexes on existing ones, so
    Alembic remains the source of truth.

    Importing `app.models` here ensures every model is registered with
    `Base.metadata` before we run create_all.
    """
    import app.models  # noqa: F401  — register all models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Columns that need to be added to *existing* tables — `create_all`
# only handles new tables, not new columns. Each entry is run
# idempotently at startup if AUTO_CREATE_TABLES is on.
#   (table, column, column_definition, optional_fk_constraint_target)
_PENDING_COLUMNS: list[tuple[str, str, str, str | None]] = [
    (
        "exam_questions",
        "course_id",
        "INT NULL",
        "lms_courses(id) ON DELETE SET NULL",
    ),
    ("sales_leads", "won_approval_status", "VARCHAR(16) NULL", None),
    ("sales_leads", "won_rejection_reason", "VARCHAR(500) NULL", None),
    ("sales_leads", "won_requested_at", "DATETIME NULL", None),
    ("sales_leads", "won_decided_at", "DATETIME NULL", None),
    ("sales_leads", "won_decided_by_user_id", "INT NULL", None),
    ("exam_certificates", "certificate_type", "VARCHAR(32) NULL", None),
    ("exam_certificates", "body_text", "VARCHAR(1000) NULL", None),
    ("exam_certificates", "file_key", "VARCHAR(500) NULL", None),
    ("exam_certificates", "file_name", "VARCHAR(255) NULL", None),
    ("exam_certificates", "mime_type", "VARCHAR(100) NULL", None),
    (
        "company_policies",
        "requires_acknowledgement",
        "BOOLEAN NOT NULL DEFAULT TRUE",
        None,
    ),
    ("company_policies", "revision", "INT NOT NULL DEFAULT 1", None),
    (
        "sales_targets",
        "metric",
        "VARCHAR(24) NOT NULL DEFAULT 'sales_amount'",
        None,
    ),
    (
        "job_postings",
        "published_to_app",
        "BOOLEAN NOT NULL DEFAULT FALSE",
        None,
    ),
    ("report_saved", "file_url", "VARCHAR(500) NULL", None),
    ("report_saved", "file_name", "VARCHAR(255) NULL", None),
    ("report_saved", "file_size", "INT NULL", None),
    ("report_saved", "file_mime", "VARCHAR(120) NULL", None),
    ("resignations", "documents", "JSON NULL", None),
    (
        "resignations",
        "separation_type",
        "VARCHAR(16) NOT NULL DEFAULT 'resignation'",
        None,
    ),
    (
        "employees",
        "resignation_unlocked",
        "BOOLEAN NOT NULL DEFAULT FALSE",
        None,
    ),
    (
        "employees",
        "pf_opt_out",
        "BOOLEAN NOT NULL DEFAULT FALSE",
        None,
    ),
    (
        "employees",
        "pf_basic_cap_override",
        "DECIMAL(10,2) NULL",
        None,
    ),
    (
        "employees",
        "esic_force_exempt",
        "BOOLEAN NOT NULL DEFAULT FALSE",
        None,
    ),
    ("employees", "pt_state", "VARCHAR(64) NULL", None),
    ("employees", "pf_number", "VARCHAR(32) NULL", None),
    ("employees", "uan_number", "VARCHAR(20) NULL", None),
    ("employees", "esic_number", "VARCHAR(20) NULL", None),
    ("employees", "insurance_company", "VARCHAR(160) NULL", None),
    ("employees", "insurance_policy_no", "VARCHAR(64) NULL", None),
    (
        "employees",
        "attendance_cycle_start_day",
        "INT NOT NULL DEFAULT 1",
        None,
    ),
    (
        "leave_types",
        "is_paid",
        "BOOLEAN NOT NULL DEFAULT TRUE",
        None,
    ),
    (
        "leave_types",
        "applies_sandwich_rule",
        "BOOLEAN NOT NULL DEFAULT FALSE",
        None,
    ),
    (
        "leave_types",
        "applies_to_genders",
        "VARCHAR(16) NOT NULL DEFAULT 'm,f'",
        None,
    ),
    (
        "leave_types",
        "requires_confirmation",
        "BOOLEAN NOT NULL DEFAULT FALSE",
        None,
    ),
    (
        "employee_probation",
        "phase",
        "VARCHAR(16) NOT NULL DEFAULT 'probation'",
        None,
    ),
    ("payslips", "days_present", "DECIMAL(5,2) NOT NULL DEFAULT 0", None),
    ("payslips", "days_paid_leave", "DECIMAL(5,2) NOT NULL DEFAULT 0", None),
    ("payslips", "days_unpaid_leave", "DECIMAL(5,2) NOT NULL DEFAULT 0", None),
    ("payslips", "days_absent", "DECIMAL(5,2) NOT NULL DEFAULT 0", None),
    ("payslips", "days_holiday", "DECIMAL(5,2) NOT NULL DEFAULT 0", None),
    ("payslips", "days_weekoff", "DECIMAL(5,2) NOT NULL DEFAULT 0", None),
    ("payslips", "days_sandwich", "DECIMAL(5,2) NOT NULL DEFAULT 0", None),
    ("payslips", "is_final_settlement", "BOOLEAN NOT NULL DEFAULT FALSE", None),
    ("payslips", "on_hold", "BOOLEAN NOT NULL DEFAULT FALSE", None),
    ("payslips", "pf_wages", "DECIMAL(12,2) NOT NULL DEFAULT 0", None),
    ("payslips", "eps_wages", "DECIMAL(12,2) NOT NULL DEFAULT 0", None),
    ("payslips", "edli_wages", "DECIMAL(12,2) NOT NULL DEFAULT 0", None),
    ("pf_wage_ceilings", "edli_cap_amount", "DECIMAL(12,2) NOT NULL DEFAULT 15000", None),
    ("employees", "eps_member", "BOOLEAN NOT NULL DEFAULT TRUE", None),
    ("refresh_tokens", "rotated_at", "DATETIME NULL", None),
    ("payroll_runs", "cycle_start_day", "INT NOT NULL DEFAULT 1", None),
    (
        "payroll_runs",
        "disbursed",
        "BOOLEAN NOT NULL DEFAULT FALSE",
        None,
    ),
    ("payroll_runs", "disbursed_at", "DATETIME NULL", None),
    ("payroll_runs", "disbursed_by", "INT NULL", None),
    ("attendance", "is_late", "BOOLEAN NOT NULL DEFAULT FALSE", None),
    ("attendance", "late_remark", "VARCHAR(255) NULL", None),
    ("employees", "backdate_from", "DATE NULL", None),
    ("employees", "backdate_to", "DATE NULL", None),
    (
        "leave_balances",
        "adjustment",
        "DECIMAL(6,2) NOT NULL DEFAULT 0",
        None,
    ),
    ("assets", "brand", "VARCHAR(80) NULL", None),
    ("assets", "model", "VARCHAR(120) NULL", None),
    ("assets", "specs", "JSON NULL", None),
    ("assets", "parent_asset_id", "INT NULL", "assets(id) ON DELETE SET NULL"),
    ("asset_assignments", "received_by", "INT NULL", "users(id) ON DELETE SET NULL"),
    ("departments", "enabled_modules", "JSON NULL", None),
    ("departments", "leave_approver_user_ids", "JSON NULL", None),
]


# Columns whose type changes on existing tables, applied when the live
# column still has the old DATA_TYPE:
#   (table, column, new_definition, old_data_type)
_PENDING_TYPE_CHANGES: list[tuple[str, str, str, str]] = [
    # Fixed lists became editable / extended.
    ("assets", "category", "VARCHAR(48) NOT NULL DEFAULT 'other'", "enum"),
    ("assets", "condition", "VARCHAR(16) NOT NULL DEFAULT 'working'", "enum"),
    ("asset_assignments", "return_condition", "VARCHAR(16) NULL", "enum"),
]

# Idempotent data fixes run after the schema changes.
_DATA_FIXES: list[str] = [
    # Old asset conditions -> working / damaged / not_working / expired.
    "UPDATE assets SET `condition` = 'working' "
    "WHERE `condition` IN ('new', 'good', 'fair')",
    "UPDATE assets SET `condition` = 'expired' WHERE `condition` = 'retired'",
    "UPDATE asset_assignments SET return_condition = 'working' "
    "WHERE return_condition IN ('good', 'fair')",
]


async def sync_columns() -> None:
    """Add any columns listed in _PENDING_COLUMNS that are missing
    from the live schema. Safe to call repeatedly; existing columns
    are skipped and FK constraint failures are swallowed.

    Logs each ALTER it runs (or skips), and re-raises with an
    actionable message if it can't apply a needed change so the
    operator sees something useful in journalctl."""
    import logging

    from sqlalchemy import text

    log = logging.getLogger(__name__)

    async with engine.begin() as conn:
        # Resolve the live database name once so log messages and the
        # actionable runbook on failure are fully qualified.
        dbname = (await conn.execute(text("SELECT DATABASE()"))).scalar() or ""
        qual = lambda t: f"{dbname}.{t}" if dbname else t  # noqa: E731

        for table, column, col_def, fk in _PENDING_COLUMNS:
            exists = (
                await conn.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() "
                        "AND TABLE_NAME = :t AND COLUMN_NAME = :c"
                    ),
                    {"t": table, "c": column},
                )
            ).scalar()
            if exists:
                log.info("sync_columns: %s.%s already present", qual(table), column)
                continue

            try:
                await conn.execute(
                    text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {col_def}")
                )
                log.info("sync_columns: added %s.%s", qual(table), column)
            except Exception as e:
                log.error(
                    "sync_columns: FAILED to add %s.%s — %s. "
                    "Run this once as a privileged DB user:\n"
                    "  ALTER TABLE %s ADD COLUMN %s %s;",
                    qual(table), column, e, qual(table), column, col_def,
                )
                raise

            try:
                await conn.execute(
                    text(
                        f"CREATE INDEX `idx_{table}_{column}` "
                        f"ON `{table}` (`{column}`)"
                    )
                )
            except Exception as e:
                log.warning(
                    "sync_columns: index for %s.%s skipped — %s",
                    qual(table), column, e,
                )

            if fk:
                try:
                    await conn.execute(
                        text(
                            f"ALTER TABLE `{table}` "
                            f"ADD CONSTRAINT `fk_{table}_{column}` "
                            f"FOREIGN KEY (`{column}`) REFERENCES {fk}"
                        )
                    )
                except Exception as e:
                    log.warning(
                        "sync_columns: FK %s.%s -> %s skipped — %s",
                        qual(table), column, fk, e,
                    )

        for table, column, col_def, old_type in _PENDING_TYPE_CHANGES:
            current = (
                await conn.execute(
                    text(
                        "SELECT DATA_TYPE FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() "
                        "AND TABLE_NAME = :t AND COLUMN_NAME = :c"
                    ),
                    {"t": table, "c": column},
                )
            ).scalar()
            if current is None or current.lower() != old_type:
                continue
            try:
                await conn.execute(
                    text(f"ALTER TABLE `{table}` MODIFY COLUMN `{column}` {col_def}")
                )
                log.info("sync_columns: changed %s.%s to %s", qual(table), column, col_def)
            except Exception as e:
                log.error(
                    "sync_columns: FAILED to change %s.%s — %s. Run once:\n"
                    "  ALTER TABLE %s MODIFY COLUMN %s %s;",
                    qual(table), column, e, qual(table), column, col_def,
                )
                raise

        for stmt in _DATA_FIXES:
            await conn.execute(text(stmt))
