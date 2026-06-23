"""
System Integration Tests
"""

import requests

BACKEND_URL = "http://localhost:8080"
AI_URL = "http://localhost:8000"


def test_backend_health():
    response = requests.get(
        f"{BACKEND_URL}/actuator/health"
    )
    assert response.status_code == 200


def test_database_connectivity():
    response = requests.get(
        f"{BACKEND_URL}/actuator/health"
    )
    assert response.status_code == 200


def test_redis_connectivity():
    response = requests.get(
        f"{BACKEND_URL}/actuator/health"
    )
    assert response.status_code == 200


def test_aiml_service_availability():
    try:
        response = requests.get(
            f"{AI_URL}/health"
        )
        assert response.status_code == 200
    except Exception:
        assert False, "AI/ML service unavailable"


def test_frontend_backend_integration():
    response = requests.get(
        f"{BACKEND_URL}/api/v1/account/summary"
    )

    assert response.status_code in [
        200,
        401,
        403
    ]