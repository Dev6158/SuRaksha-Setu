import requests
import tempfile

BASE_URL = "http://localhost:8080"


def test_ai_analyze_endpoint():

    with tempfile.NamedTemporaryFile(
        suffix=".txt",
        delete=False
    ) as temp:

        temp.write(b"sample document")
        temp.flush()

        with open(temp.name, "rb") as f:

            response = requests.post(
                f"{BASE_URL}/api/v1/ai/analyze",
                files={
                    "file": f
                }
            )

        assert response.status_code in [
            200,
            400,
            401,
            403
        ]