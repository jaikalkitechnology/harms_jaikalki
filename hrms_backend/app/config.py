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
