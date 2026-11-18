from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env", ".env.pilot"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    secret_key: str = "dev-secret-key-replace-in-production"

    # Security & JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720
    refresh_token_expire_days: int = 7
    refresh_token_grace_window_seconds: int = 15

    # Rate Limiting
    rate_limit_auth_requests: int = 5
    rate_limit_upload_requests: int = 10
    rate_limit_window_seconds: int = 60
    rate_limit_account_max_failures: int = 5
    rate_limit_account_lockout_seconds: int = 900

    # Trusted Reverse Proxies (CIDRs)
    trusted_proxies: str = "127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

    @property
    def trusted_proxies_list(self) -> list[str]:
        return [p.strip() for p in self.trusted_proxies.split(",") if p.strip()]

    @property
    def rate_limit_login_per_minute(self) -> int:
        return self.rate_limit_auth_requests

    @property
    def rate_limit_upload_per_minute(self) -> int:
        return self.rate_limit_upload_requests

    # Database
    database_url: str = "postgresql://visionforensics_app:app_secure_pass_2026@localhost:5433/visionforensics"
    migration_database_url: str = "postgresql://visionforensics_migrator:migrator_secure_pass_2026@localhost:5433/visionforensics"

    # Storage
    upload_dir: str = "uploads"
    processed_dir: str = "processed"
    reports_dir: str = "reports"
    heatmaps_dir: str = "heatmaps"

    # Upload limits
    max_file_size_mb: int = 20
    max_image_dimension: int = 10000
    max_pdf_pages: int = 50

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080,https://localhost:8443,https://127.0.0.1:8443,http://visionforensics.local:8080,https://visionforensics.local:8443"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env.lower() in ("production", "pilot"):
            if self.secret_key in ("change-me", "dev-secret-key-replace-in-production", ""):
                raise ValueError(f"{self.app_env.capitalize()} security failure: SECRET_KEY must be a strong random secret.")
            if self.app_debug:
                raise ValueError(f"{self.app_env.capitalize()} security failure: APP_DEBUG must be disabled (False).")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
