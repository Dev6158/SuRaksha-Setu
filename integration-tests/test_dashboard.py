import requests

BASE_URL = "http://localhost:8080"


def test_account_summary():

    response = requests.get(
        f"{BASE_URL}/api/v1/account/summary"
    )

    assert response.status_code in [
        200,
        401,
        403
    ]


def test_transactions():

    response = requests.get(
        f"{BASE_URL}/api/v1/transactions"
    )

    assert response.status_code in [
        200,
        401,
        403
    ]


def test_monthly_stats():

    response = requests.get(
        f"{BASE_URL}/api/v1/account/monthly-stats"
    )

    assert response.status_code in [
        200,
        401,
        403
    ]