from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PageInfo(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class JobListResponse(BaseModel):
    items: list[dict[str, Any]]
    pagination: PageInfo


class StatisticsResponse(BaseModel):
    total_jobs: int
    successful_jobs: int
    partial_jobs: int
    failed_jobs: int
    new_jobs: int
    last_updated_at: str | None = None


class LastRunResponse(BaseModel):
    batch_at: str | None = None
    status: str
    total_listings: int = 0
    successful_details: int = 0
    partial_details: int = 0
    failed_details: int = 0


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str


class ErrorResponse(BaseModel):
    detail: str = Field(..., min_length=1)
