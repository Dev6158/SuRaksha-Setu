import requests

BASE_URL = "http://localhost:8080"


def test_login_endpoint():

    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "username": "test",
            "password": "test"
        }
    )

    assert response.status_code in [
        200,
        400,
        401
    ]


def test_register_endpoint():

    response = requests.post(
        f"{BASE_URL}/register",
        json={
            "username": "integration_test",
            "password": "password123"
        }
    )

    assert response.status_code in [
        200,
        201,
        400
    ]


def test_otp_verify_endpoint():

    response = requests.post(
        f"{BASE_URL}/otp/verify",
        json={
            "otp": "123456",
            "session_id": "test-session"
        }
    )

    assert response.status_code in [
        200,
        400,
        401
    ]