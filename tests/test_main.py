"""
Unit tests for the Finance Analyzer API
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "finance-analyzer"}


def test_home_page():
    """Test home page loads"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_analyze_text_valid():
    """Test text analysis with valid input"""
    response = client.post(
        "/analyze",
        json={"text": "دفعت 50 جنيه في كارفور على خضار"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert "amount" in data["analysis"]
    assert "category" in data["analysis"]


def test_analyze_text_empty():
    """Test text analysis with empty input"""
    response = client.post(
        "/analyze",
        json={"text": ""}
    )
    assert response.status_code == 422  # Validation error


def test_analyze_text_too_long():
    """Test text analysis with too long input"""
    response = client.post(
        "/analyze",
        json={"text": "a" * 1001}
    )
    assert response.status_code == 422  # Validation error


def test_voice_no_file():
    """Test voice analysis without file"""
    response = client.post("/voice")
    assert response.status_code == 422  # Missing required field


def test_api_docs():
    """Test API documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200
