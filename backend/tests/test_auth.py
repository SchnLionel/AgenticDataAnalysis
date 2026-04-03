def test_register_user(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login_success(client):
    # First, register a user
    client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "password"
    })
    
    # Then, login
    response = client.post("/api/v1/auth/login", data={
        "username": "login@example.com",
        "password": "password"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    # Register a user
    client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com",
        "password": "password"
    })
    
    # Login with wrong password
    response = client.post("/api/v1/auth/login", data={
        "username": "wrong@example.com",
        "password": "wrong"
    })
    assert response.status_code == 401
