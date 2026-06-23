import requests

BASE_URL = "http://localhost:8080"

def test_login_endpoint():
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "username": "test",
            "password": "password123"
        }
    )

    assert response.status_code in [200, 400, 401]


def test_register_endpoint():
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "username": "integration_test",
            "password": "password123"
        }
    )

    assert response.status_code in [200, 201, 400]


def test_otp_verify_endpoint():
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/otp/verify",
        json={
            "username": "integration_test",
            "otp": "123456"
        }
    )

    assert response.status_code in [200, 400, 401]