from math import ceil
from io import StringIO
import csv
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.app.config import Settings, get_settings
from backend.app.rate_limit import RateLimiter
from backend.app.repository import LegacyDataError, LegacyJsonRepository
from backend.app.schemas import (
    HealthResponse,
    JobListResponse,
    LastRunResponse,
    PageInfo,
    StatisticsResponse,
)

app = FastAPI(
    title="MagangHub Job Finder API",
    version="1.0.0",
    description="Public read-only API backed by the existing JSON data.",
)
_rate_limiter = RateLimiter(get_settings().rate_limit_window_seconds)


def repository(settings: Settings = Depends(get_settings)) -> LegacyJsonRepository:
    return LegacyJsonRepository(settings.data_dir)


def limiter() -> RateLimiter:
    return _rate_limiter


def client_key(request: Request, settings: Settings) -> str:
    direct_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if direct_ip in settings.trusted_proxy_ip_list() and forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or direct_ip
    return direct_ip


def enforce_rate_limit(
    request: Request,
    endpoint: str,
    limit: int,
    rate_limiter: RateLimiter,
    settings: Settings,
) -> None:
    if not rate_limiter.allow(client_key(request, settings), endpoint, limit):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(settings.rate_limit_window_seconds)},
        )


def handle_data_error(error: LegacyDataError) -> HTTPException:
    return HTTPException(status_code=503, detail="Stored data is unavailable")


def job_listing(job: dict) -> dict:
    listing = job.get("listing")
    return listing if isinstance(listing, dict) else {}


def job_matches(
    job: dict,
    search: str | None,
    location: str | None,
    status: str | None,
    opportunity: str | None,
) -> bool:
    listing = job_listing(job)
    if search:
        haystack = " ".join(
            str(listing.get(field, ""))
            for field in ("title", "company", "location", "majors_raw")
        ).casefold()
        if search.casefold() not in haystack:
            return False
    if location and location.casefold() not in str(
        listing.get("location", "")
    ).casefold():
        return False
    if status and str(job.get("scraping_status", "")).casefold() != status.casefold():
        return False
    if opportunity and opportunity.casefold() not in str(
        listing.get("opportunity", "")
    ).casefold():
        return False
    return True


def paginate(items: list[dict], page: int, page_size: int) -> tuple[list[dict], PageInfo]:
    total = len(items)
    start = (page - 1) * page_size
    return items[start:start + page_size], PageInfo(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=ceil(total / page_size) if total else 0,
    )


settings = get_settings()
if settings.cors_origin_list():
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_methods=["GET"],
        allow_headers=["*"],
    )


@app.get("/api/v1/jobs", response_model=JobListResponse)
def get_jobs(
    request: Request,
    response: Response,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=100)] = None,
    location: Annotated[str | None, Query(max_length=100)] = None,
    status: Annotated[str | None, Query(pattern="^(success|partial|failed)$")] = None,
    opportunity: Annotated[str | None, Query(max_length=100)] = None,
    repo: LegacyJsonRepository = Depends(repository),
    settings: Settings = Depends(get_settings),
    rate_limiter: RateLimiter = Depends(limiter),
) -> JobListResponse:
    enforce_rate_limit(
        request, "jobs-search" if search or location or status or opportunity else "jobs",
        settings.rate_limit_search if search or location or status or opportunity else settings.rate_limit_jobs,
        rate_limiter, settings,
    )
    try:
        jobs = [
            job for job in repo.jobs()
            if job_matches(job, search, location, status, opportunity)
        ]
    except LegacyDataError as error:
        raise handle_data_error(error) from error
    items, pagination = paginate(jobs, page, page_size)
    response.headers["Cache-Control"] = "public, max-age=30"
    return JobListResponse(items=items, pagination=pagination)


@app.get("/api/v1/jobs/{job_id:path}")
def get_job(
    job_id: str,
    request: Request,
    repo: LegacyJsonRepository = Depends(repository),
    settings: Settings = Depends(get_settings),
    rate_limiter: RateLimiter = Depends(limiter),
) -> dict:
    enforce_rate_limit(
        request, "job-detail", settings.rate_limit_job_detail,
        rate_limiter, settings,
    )
    try:
        for job in repo.jobs():
            listing = job_listing(job)
            if str(listing.get("url", "")) == job_id or str(
                listing.get("external_id", "")
            ) == job_id:
                return job
    except LegacyDataError as error:
        raise handle_data_error(error) from error
    raise HTTPException(status_code=404, detail="Job not found")


@app.get("/api/v1/statistics", response_model=StatisticsResponse)
def get_statistics(
    request: Request,
    repo: LegacyJsonRepository = Depends(repository),
    settings: Settings = Depends(get_settings),
    rate_limiter: RateLimiter = Depends(limiter),
) -> StatisticsResponse:
    enforce_rate_limit(
        request, "statistics", settings.rate_limit_statistics,
        rate_limiter, settings,
    )
    try:
        jobs = repo.jobs()
        report = repo.monitoring_report()
    except LegacyDataError as error:
        raise handle_data_error(error) from error
    statuses = [job.get("scraping_status") for job in jobs]
    return StatisticsResponse(
        total_jobs=len(jobs),
        successful_jobs=statuses.count("success"),
        partial_jobs=statuses.count("partial"),
        failed_jobs=statuses.count("failed"),
        new_jobs=int(report.get("summary", {}).get("new_jobs", 0)),
        last_updated_at=report.get("generated_at"),
    )


@app.get("/api/v1/monitoring/summary")
def get_monitoring_summary(
    request: Request,
    repo: LegacyJsonRepository = Depends(repository),
    settings: Settings = Depends(get_settings),
    rate_limiter: RateLimiter = Depends(limiter),
) -> dict:
    enforce_rate_limit(
        request, "monitoring-summary", settings.rate_limit_statistics,
        rate_limiter, settings,
    )
    try:
        return repo.monitoring_report().get("summary", {})
    except LegacyDataError as error:
        raise handle_data_error(error) from error


@app.get("/api/v1/monitoring/changes")
def get_monitoring_changes(
    request: Request,
    status: Annotated[str | None, Query(pattern="^(detected|confirmed|reverted)$")] = None,
    repo: LegacyJsonRepository = Depends(repository),
    settings: Settings = Depends(get_settings),
    rate_limiter: RateLimiter = Depends(limiter),
) -> list[dict]:
    enforce_rate_limit(
        request, "monitoring-changes", settings.rate_limit_statistics,
        rate_limiter, settings,
    )
    try:
        changes = repo.changes()
    except LegacyDataError as error:
        raise handle_data_error(error) from error
    return [
        item for item in changes
        if status is None or item.get("status") == status
    ]


@app.get("/api/v1/scraping/last-run", response_model=LastRunResponse)
def get_last_run(repo: LegacyJsonRepository = Depends(repository)) -> LastRunResponse:
    try:
        return LastRunResponse(**repo.last_run())
    except LegacyDataError as error:
        raise handle_data_error(error) from error


@app.get("/api/v1/exports/jobs.csv")
def export_jobs(
    request: Request,
    repo: LegacyJsonRepository = Depends(repository),
    settings: Settings = Depends(get_settings),
    rate_limiter: RateLimiter = Depends(limiter),
) -> StreamingResponse:
    enforce_rate_limit(
        request, "export", settings.rate_limit_export,
        rate_limiter, settings,
    )
    try:
        jobs = repo.jobs()
    except LegacyDataError as error:
        raise handle_data_error(error) from error

    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["url", "title", "company", "location", "status"])

    def safe_csv_value(value: object) -> str:
        text = str(value)
        if text.startswith(("=", "+", "-", "@")):
            return "'" + text
        return text

    for job in jobs:
        listing = job_listing(job)
        writer.writerow([
            safe_csv_value(listing.get("url", "")),
            safe_csv_value(listing.get("title", "")),
            safe_csv_value(listing.get("company", "")),
            safe_csv_value(listing.get("location", "")),
            safe_csv_value(job.get("scraping_status", "")),
        ])
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="jobs.csv"'},
    )


@app.get("/health/live", response_model=HealthResponse)
def health_live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=HealthResponse)
def health_ready(
    repo: LegacyJsonRepository = Depends(repository),
) -> HealthResponse:
    try:
        repo.jobs()
    except LegacyDataError as error:
        raise HTTPException(status_code=503, detail="Data store unavailable") from error
    return HealthResponse(status="ready")
