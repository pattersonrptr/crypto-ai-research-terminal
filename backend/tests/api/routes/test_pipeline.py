"""TDD tests for the pipeline/collect-now API endpoints.

POST /pipeline/collect-now — triggers collection job asynchronously.
GET  /pipeline/status/{job_id} — returns job progress.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.pipeline import _job_registry, router

# ---------------------------------------------------------------------------
# Test app fixture
# ---------------------------------------------------------------------------

_app = FastAPI()
_app.include_router(router, prefix="/pipeline")
_client = TestClient(_app)


# ---------------------------------------------------------------------------
# POST /pipeline/collect-now
# ---------------------------------------------------------------------------


class TestCollectNowEndpoint:
    """Tests for POST /pipeline/collect-now."""

    def setup_method(self) -> None:
        """Clear job registry between tests."""
        _job_registry.clear()

    def test_collect_now_returns_202(self) -> None:
        """POST /pipeline/collect-now must return 202 Accepted."""
        with patch("app.api.routes.pipeline._run_job_in_background"):
            response = _client.post("/pipeline/collect-now")
        assert response.status_code == 202

    def test_collect_now_returns_job_id(self) -> None:
        """POST /pipeline/collect-now must return a job_id."""
        with patch("app.api.routes.pipeline._run_job_in_background"):
            response = _client.post("/pipeline/collect-now")
        data = response.json()
        assert "job_id" in data
        # job_id must be a valid UUID
        uuid.UUID(data["job_id"])

    def test_collect_now_registers_pending_job(self) -> None:
        """POST /pipeline/collect-now must register job as 'pending'."""
        with patch("app.api.routes.pipeline._run_job_in_background"):
            response = _client.post("/pipeline/collect-now")
        job_id = response.json()["job_id"]
        assert job_id in _job_registry
        assert _job_registry[job_id]["status"] == "pending"


# ---------------------------------------------------------------------------
# GET /pipeline/status/{job_id}
# ---------------------------------------------------------------------------


class TestJobStatusEndpoint:
    """Tests for GET /pipeline/status/{job_id}."""

    def setup_method(self) -> None:
        """Clear job registry between tests."""
        _job_registry.clear()

    def test_status_returns_404_for_unknown_job(self) -> None:
        """GET /pipeline/status/<unknown> must return 404."""
        response = _client.get(f"/pipeline/status/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_status_returns_pending_job(self) -> None:
        """GET /pipeline/status/<id> must return pending status."""
        job_id = str(uuid.uuid4())
        _job_registry[job_id] = {"status": "pending", "detail": ""}
        response = _client.get(f"/pipeline/status/{job_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_status_returns_completed_job(self) -> None:
        """GET /pipeline/status/<id> must return completed status."""
        job_id = str(uuid.uuid4())
        _job_registry[job_id] = {"status": "completed", "detail": "42 tokens"}
        response = _client.get(f"/pipeline/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "42" in data["detail"]

    def test_status_returns_failed_job(self) -> None:
        """GET /pipeline/status/<id> must return failed status."""
        job_id = str(uuid.uuid4())
        _job_registry[job_id] = {"status": "failed", "detail": "connection error"}
        response = _client.get(f"/pipeline/status/{job_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "failed"
