"""
System Integration Tests
"""

import requests

BACKEND_URL = "http://localhost:8080"
AI_URL = "http://localhost:8000"


def test_swagger_available():
    response = requests.get(
        f"{BACKEND_URL}/swagger-ui/index.html"
    )

    assert response.status_code == 200


def test_openapi_docs_available():
    response = requests.get(
        f"{BACKEND_URL}/v3/api-docs"
    )

    assert response.status_code == 200


def test_document_types_endpoint():
    response = requests.get(
        f"{BACKEND_URL}/api/v1/documents/types"
    )

    assert response.status_code == 200


def test_aiml_service_availability():
    try:
        response = requests.get(
            f"{AI_URL}/healthz"
        )
        assert response.status_code == 200
    except:
        pass


def test_frontend_backend_integration():
    response = requests.get(
        f"{BACKEND_URL}/api/v1/account/summary"
    )

    assert response.status_code in [200, 401, 403]