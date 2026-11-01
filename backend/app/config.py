from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MAGANGHUB_",
        env_file=".env",
        extra="ignore",
    )

    data_dir: Path = Path("output")
    cors_origins: str = ""
    trusted_proxy_ips: str = ""
    rate_limit_window_seconds: int = 60
    rate_limit_jobs: int = 60
    rate_limit_job_detail: int = 60
    rate_limit_statistics: int = 30
    rate_limit_search: int = 30
    rate_limit_export: int = 5

    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def trusted_proxy_ip_list(self) -> set[str]:
        return {
            ip.strip()
            for ip in self.trusted_proxy_ips.split(",")
            if ip.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
