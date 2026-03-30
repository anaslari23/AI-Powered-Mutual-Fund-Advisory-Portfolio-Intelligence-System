import requests
import json

# Setup
BASE_URL = "http://localhost:8000"
email = "test_err@test.com"
requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": "password123", "name": "Tester"})
login_res = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": "password123"})
token = login_res.json()["access_token"]

# Test Create
payload = {"name": "Test", "age": 30}
create_res = requests.post(f"{BASE_URL}/clients/", json=payload, headers={"Authorization": f"Bearer {token}"})

print(f"Status: {create_res.status_code}")
print(f"Body: {create_res.text}")
