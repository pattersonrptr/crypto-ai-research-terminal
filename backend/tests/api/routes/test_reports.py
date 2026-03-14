"""Tests for reports API endpoints.

TDD RED phase: Tests written before implementation.
"""

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.routes.reports import router


@pytest.fixture
def app() -> FastAPI:
    """Create FastAPI app with reports router."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/reports")
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestGetTokenReport:
    """Tests for GET /reports/token/{symbol} endpoint."""

    def test_get_token_report_markdown_returns_content(self, client: TestClient) -> None:
        """Test that token report returns markdown content."""
        response = client.get(
            "/reports/token/SOL",
            params={"format": "markdown"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "text/markdown" in response.headers.get("content-type", "")
        content = response.text
        assert "SOL" in content or "Solana" in content

    def test_get_token_report_pdf_returns_bytes(self, client: TestClient) -> None:
        """Test that token report returns PDF bytes."""
        response = client.get(
            "/reports/token/SOL",
            params={"format": "pdf"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "application/pdf" in response.headers.get("content-type", "")
        # PDF files start with %PDF
        assert response.content[:4] == b"%PDF"

    def test_get_token_report_default_format_is_markdown(self, client: TestClient) -> None:
        """Test that default format is markdown."""
        response = client.get("/reports/token/BTC")

        assert response.status_code == status.HTTP_200_OK
        assert "text/markdown" in response.headers.get("content-type", "")

    def test_get_token_report_invalid_format_returns_error(self, client: TestClient) -> None:
        """Test that invalid format returns 422."""
        response = client.get(
            "/reports/token/SOL",
            params={"format": "invalid"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_token_report_includes_content_disposition(self, client: TestClient) -> None:
        """Test that response includes download filename."""
        response = client.get(
            "/reports/token/SOL",
            params={"format": "markdown"},
        )

        assert response.status_code == status.HTTP_200_OK
        content_disp = response.headers.get("content-disposition", "")
        assert "SOL" in content_disp or "sol" in content_disp.lower()


class TestGetMarketReport:
    """Tests for GET /reports/market endpoint."""

    def test_get_market_report_markdown_returns_content(self, client: TestClient) -> None:
        """Test that market report returns markdown content."""
        response = client.get(
            "/reports/market",
            params={"format": "markdown"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "text/markdown" in response.headers.get("content-type", "")
        content = response.text
        assert "Market" in content or "market" in content

    def test_get_market_report_pdf_returns_bytes(self, client: TestClient) -> None:
        """Test that market report returns PDF bytes."""
        response = client.get(
            "/reports/market",
            params={"format": "pdf"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "application/pdf" in response.headers.get("content-type", "")
        assert response.content[:4] == b"%PDF"

    def test_get_market_report_default_format_is_markdown(self, client: TestClient) -> None:
        """Test that default format is markdown."""
        response = client.get("/reports/market")

        assert response.status_code == status.HTTP_200_OK
        assert "text/markdown" in response.headers.get("content-type", "")

    def test_get_market_report_includes_content_disposition(self, client: TestClient) -> None:
        """Test that response includes download filename."""
        response = client.get(
            "/reports/market",
            params={"format": "pdf"},
        )

        assert response.status_code == status.HTTP_200_OK
        content_disp = response.headers.get("content-disposition", "")
        assert "market" in content_disp.lower()


class TestReportFormats:
    """Tests for report format validation."""

    def test_format_enum_accepts_markdown(self, client: TestClient) -> None:
        """Test markdown format is accepted."""
        response = client.get(
            "/reports/token/ETH",
            params={"format": "markdown"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_format_enum_accepts_pdf(self, client: TestClient) -> None:
        """Test PDF format is accepted."""
        response = client.get(
            "/reports/token/ETH",
            params={"format": "pdf"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_format_is_case_sensitive(self, client: TestClient) -> None:
        """Test format parameter is case-sensitive."""
        response = client.get(
            "/reports/token/ETH",
            params={"format": "MARKDOWN"},
        )

        # Should fail validation as enum is lowercase
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestReportContent:
    """Tests for report content quality."""

    def test_token_report_contains_required_sections(self, client: TestClient) -> None:
        """Test token report has all required sections."""
        response = client.get("/reports/token/SOL")

        content = response.text.lower()
        # Should contain key sections
        assert "price" in content or "market" in content
        assert "score" in content or "risk" in content

    def test_market_report_contains_required_sections(self, client: TestClient) -> None:
        """Test market report has all required sections."""
        response = client.get("/reports/market")

        content = response.text.lower()
        # Should contain key sections
        assert "market" in content
