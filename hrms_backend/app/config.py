from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Jaikalki HRMS"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    API_ADMIN_PREFIX: str = "/api/admin"

    COMPANY_NAME: str = "Jaikalki Technology Pvt Ltd"
    COMPANY_ADDRESS: str = (
        "Sh N B1/A Ground Floor, Mahavir Nagar, Deepak Hospital, "
        "Mira Road, Thane-401107 Maharashtra"
    )
    EMPLOYEE_CODE_PREFIX: str = "JKT"

    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # If True, the FastAPI lifespan startup hook runs
    # `Base.metadata.create_all()` so any new model tables are added
    # without a manual `alembic upgrade head`. Convenient for dev /
    # first boot. Leave False in production — Alembic migrations are
    # the source of truth there.
    AUTO_CREATE_TABLES: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    CORS_ORIGINS: List[str] = Field(default_factory=list)

    # Public base URL of this API (used in PDFs, emails, OAuth callbacks).
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # Office geo-fence (default: Jaikalki Mira Road)
    OFFICE_LAT: float = 19.2853
    OFFICE_LNG: float = 72.8533
    OFFICE_RADIUS_M: int = 200

    # Justice Portal AES-GCM-256 encryption key (base64, 32 bytes raw).
    # If unset, derives a deterministic key from JWT_SECRET_KEY so dev still
    # works — but production MUST set its own.
    JUSTICE_ENCRYPTION_KEY: Optional[str] = None

    # ── Email (SMTP) ──────────────────────────────────────────────
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025  # MailHog default for dev
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = False
    SMTP_FROM_EMAIL: str = "no-reply@jaikalki.com"
    SMTP_FROM_NAME: str = "Jaikalki HRMS"
    EMAIL_ENABLED: bool = True

    # ── Mobile push (Firebase) ────────────────────────────────────
    FCM_SERVER_KEY: Optional[str] = None  # legacy HTTP API key, optional

    # ── MFA ───────────────────────────────────────────────────────
    MFA_ISSUER: str = "Jaikalki HRMS"
    MFA_REQUIRED_ROLES: List[str] = Field(
        default_factory=lambda: ["super_admin", "hr"]
    )

    # ── Password reset OTP ────────────────────────────────────────
    PASSWORD_RESET_OTP_TTL_MINUTES: int = 15
    PASSWORD_RESET_MAX_ATTEMPTS: int = 5

    # ── Celery ────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Error reporting (Sentry) ──────────────────────────────────
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    SENTRY_ENVIRONMENT: Optional[str] = None  # falls back to ENVIRONMENT

    # ── Firebase Cloud Messaging ──────────────────────────────────
    # Path to a Firebase service-account JSON file. If set, real push
    # notifications are dispatched; otherwise FCM rows are stored as
    # `pending` so dev/test environments don't depend on Firebase.
    FCM_CREDENTIALS_PATH: Optional[str] = None
    FCM_PROJECT_ID: Optional[str] = None

    # File storage backend: "local" (filesystem) or "s3" (MinIO / AWS S3)
    STORAGE_BACKEND: str = "local"

    # Local storage — used when STORAGE_BACKEND == "local". Files are
    # written under {LOCAL_STORAGE_PATH}/{key} and served back at
    # {PUBLIC_BASE_URL}{LOCAL_STORAGE_URL_PREFIX}/{key}.
    # In production, mount a host volume at LOCAL_STORAGE_PATH so files
    # survive container restarts.
    LOCAL_STORAGE_PATH: str = "/app/uploads"
    LOCAL_STORAGE_URL_PREFIX: str = "/uploads"

    # S3 / MinIO — used when STORAGE_BACKEND == "s3"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "hrms-files"
    S3_REGION: str = "us-east-1"


# Reusable MySQL table args (utf8mb4 + InnoDB) for all SQLAlchemy models.
mysql_table_args = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
