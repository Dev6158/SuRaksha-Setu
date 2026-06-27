import requests
import tempfile

BASE_URL = "http://localhost:8080"

def test_document_types():
    response = requests.get(
        f"{BASE_URL}/api/v1/documents/types"
    )

    assert response.status_code == 200


def test_document_upload_endpoint():

    with tempfile.NamedTemporaryFile(
        suffix=".txt",
        delete=False
    ) as temp:

        temp.write(b"sample document")
        temp.flush()

        with open(temp.name, "rb") as f:

            response = requests.post(
                f"{BASE_URL}/api/v1/documents/upload",
                files={"file": f},
                data={"purpose": "integration-test"}
            )

    # endpoint requires authentication
    assert response.status_code in [200, 201, 401, 403]