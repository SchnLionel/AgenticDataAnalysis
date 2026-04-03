import pytest
import io

def test_create_session(client, auth_headers):
    response = client.post(
        "/api/v1/sessions/",
        json={"title": "Test Session"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Session"
    assert "id" in data

def test_list_sessions(client, auth_headers):
    # Create two sessions
    client.post("/api/v1/sessions/", json={"title": "S1"}, headers=auth_headers)
    client.post("/api/v1/sessions/", json={"title": "S2"}, headers=auth_headers)
    
    response = client.get("/api/v1/sessions/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_upload_dataset(client, auth_headers, tmp_path):
    # Mock a CSV file
    csv_content = "name,age\nAlice,30\nBob,25"
    file = io.BytesIO(csv_content.encode('utf-8'))
    
    # We need to mock the UPLOAD_DIR or just let it create it in the current dir
    # Since we are in a test env, we should be careful.
    
    response = client.post(
        "/api/v1/sessions/upload",
        files={"file": ("test.csv", file, "text/csv")},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.csv"
    assert data["row_count"] == 2
    assert "name" in data["column_info"]

def test_unauthorized_access(client):
    response = client.get("/api/v1/sessions/")
    assert response.status_code == 401
