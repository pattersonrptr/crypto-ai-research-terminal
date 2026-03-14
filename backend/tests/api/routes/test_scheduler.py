"""Tests for GET /scheduler/status endpoint.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.main import app


class TestSchedulerStatusEndpoint:
    """GET /scheduler/status returns job health information."""

    @pytest.mark.asyncio
    async def test_scheduler_status_returns_200(self) -> None:
        mock_status = {
            "job_name": "daily_collection_job",
            "last_run": "2025-01-01T06:00:00+00:00",
            "last_status": "success",
            "error_count": 0,
            "last_error": None,
        }
        with patch(
            "app.api.routes.scheduler.get_job_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/scheduler/status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_scheduler_status_returns_job_name(self) -> None:
        mock_status = {
            "job_name": "daily_collection_job",
            "last_run": "2025-01-01T06:00:00+00:00",
            "last_status": "success",
            "error_count": 0,
            "last_error": None,
        }
        with patch(
            "app.api.routes.scheduler.get_job_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/scheduler/status")
        data = response.json()
        assert "job_name" in data
        assert data["job_name"] == "daily_collection_job"

    @pytest.mark.asyncio
    async def test_scheduler_status_returns_last_run(self) -> None:
        mock_status = {
            "job_name": "daily_collection_job",
            "last_run": "2025-01-01T06:00:00+00:00",
            "last_status": "success",
            "error_count": 0,
            "last_error": None,
        }
        with patch(
            "app.api.routes.scheduler.get_job_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/scheduler/status")
        data = response.json()
        assert data["last_run"] == "2025-01-01T06:00:00+00:00"

    @pytest.mark.asyncio
    async def test_scheduler_status_returns_last_status(self) -> None:
        mock_status = {
            "job_name": "daily_collection_job",
            "last_run": "2025-01-01T06:00:00+00:00",
            "last_status": "success",
            "error_count": 0,
            "last_error": None,
        }
        with patch(
            "app.api.routes.scheduler.get_job_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/scheduler/status")
        data = response.json()
        assert data["last_status"] == "success"

    @pytest.mark.asyncio
    async def test_scheduler_status_returns_error_count(self) -> None:
        mock_status = {
            "job_name": "daily_collection_job",
            "last_run": "2025-01-01T06:00:00+00:00",
            "last_status": "success",
            "error_count": 0,
            "last_error": None,
        }
        with patch(
            "app.api.routes.scheduler.get_job_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/scheduler/status")
        data = response.json()
        assert "error_count" in data
        assert data["error_count"] == 0

    @pytest.mark.asyncio
    async def test_scheduler_status_returns_null_fields_when_never_ran(self) -> None:
        mock_status = {
            "job_name": "daily_collection_job",
            "last_run": None,
            "last_status": None,
            "error_count": 0,
            "last_error": None,
        }
        with patch(
            "app.api.routes.scheduler.get_job_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert data["last_run"] is None
        assert data["last_status"] is None

    @pytest.mark.asyncio
    async def test_scheduler_status_returns_failure_info_when_job_failed(
        self,
    ) -> None:
        mock_status = {
            "job_name": "daily_collection_job",
            "last_run": "2025-01-02T06:00:00+00:00",
            "last_status": "failure",
            "error_count": 3,
            "last_error": "Connection timeout",
        }
        with patch(
            "app.api.routes.scheduler.get_job_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/scheduler/status")
        data = response.json()
        assert data["last_status"] == "failure"
        assert data["error_count"] == 3
        assert data["last_error"] == "Connection timeout"

    @pytest.mark.asyncio
    async def test_scheduler_status_all_jobs_endpoint_returns_list(self) -> None:
        mock_statuses = [
            {
                "job_name": "daily_collection_job",
                "last_run": "2025-01-01T06:00:00+00:00",
                "last_status": "success",
                "error_count": 0,
                "last_error": None,
            }
        ]
        with patch(
            "app.api.routes.scheduler.get_all_job_statuses",
            new_callable=AsyncMock,
            return_value=mock_statuses,
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/scheduler/status/all")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
