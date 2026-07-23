"""
Comprehensive API test script.
Run: python test_api.py
"""
import os
import sys
from fastapi.testclient import TestClient
from main import app
from database import init_db

# Initialize database tables before running tests
init_db()

client = TestClient(app)
passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  \u2705 {name}")
    else:
        failed += 1
        print(f"  \u274c {name} - {detail}")


# =============================================================================
# 1. Health Check
# =============================================================================
print("\n\U0001f3e5 Health Check")
r = client.get("/")
test("Root endpoint", r.status_code == 200)
test("Response has app name", "Extra Hours Management API" in r.json().get("app", ""))
test("Status is running", r.json().get("status") == "running")

# =============================================================================
# 2. Authentication - Register
# =============================================================================
print("\n\U0001f510 Authentication")

r = client.post("/api/auth/register", json={
    "name": "Test",
    "surname": "Admin",
    "username": "test_admin",
    "password": "test123456"
})
test("Register admin - status 201", r.status_code == 201)
test("Register returns admin data", "username" in r.json())
test("Register returns no password", "password" not in r.json())

# Register duplicate username
r = client.post("/api/auth/register", json={
    "name": "Test",
    "surname": "Admin",
    "username": "test_admin",
    "password": "test123456"
})
test("Register duplicate username - status 409", r.status_code == 409)

# =============================================================================
# 3. Authentication - Login
# =============================================================================
r = client.post("/api/auth/login", json={
    "username": "test_admin",
    "password": "test123456"
})
test("Login - status 200", r.status_code == 200)
test("Login returns access_token", "access_token" in r.json())
test("Login returns token_type bearer", r.json().get("token_type") == "bearer")
TOKEN = r.json()["access_token"]
test("Token is not empty", len(TOKEN) > 20)

# Login with wrong password
r = client.post("/api/auth/login", json={
    "username": "test_admin",
    "password": "wrong_password"
})
test("Login wrong password - status 401", r.status_code == 401)

# =============================================================================
# 4. Authentication - Get Me
# =============================================================================
r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {TOKEN}"})
test("Get me - status 200", r.status_code == 200)
test("Get me returns correct username", r.json().get("username") == "test_admin")

# Get me without token
r = client.get("/api/auth/me")
test("Get me no token - status 401", r.status_code == 401)

# Get me with invalid token
r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token_here"})
test("Get me invalid token - status 401", r.status_code == 401 or r.status_code == 403)

# =============================================================================
# 5. Persons - CRUD
# =============================================================================
print("\n\U0001f464 Persons CRUD")

# Create person
r = client.post("/api/persons/", json={
    "name": "John",
    "surname": "Doe",
    "faculty": "Engineering"
}, headers={"Authorization": f"Bearer {TOKEN}"})
test("Create person - status 201", r.status_code == 201)
test("Create person has id", "id" in r.json())
PERSON_ID = r.json()["id"]
test("Create person correct name", r.json().get("name") == "John")

# Create person without auth
r = client.post("/api/persons/", json={
    "name": "NoAuth",
    "surname": "User",
    "faculty": "Test"
})
test("Create person no auth - status 401", r.status_code == 401)

# List persons
r = client.get("/api/persons/", headers={"Authorization": f"Bearer {TOKEN}"})
test("List persons - status 200", r.status_code == 200)
test("List persons returns array", isinstance(r.json(), list))
test("List contains created person", any(p["id"] == PERSON_ID for p in r.json()))

# Get person detail
r = client.get(f"/api/persons/{PERSON_ID}", headers={"Authorization": f"Bearer {TOKEN}"})
test("Get person detail - status 200", r.status_code == 200)
test("Person detail has extra hours summary", "total_extra_hours" in r.json())

# Get non-existent person
r = client.get("/api/persons/99999", headers={"Authorization": f"Bearer {TOKEN}"})
test("Get non-existent person - status 404", r.status_code == 404)

# Update person
r = client.put(f"/api/persons/{PERSON_ID}", json={
    "faculty": "Computer Science"
}, headers={"Authorization": f"Bearer {TOKEN}"})
test("Update person - status 200", r.status_code == 200)
test("Update person faculty changed", r.json().get("faculty") == "Computer Science")

# =============================================================================
# 6. Extra Hours - CRUD
# =============================================================================
print("\n\u23f0 Extra Hours CRUD")

# Create extra hours
r = client.post("/api/extra-hours/", json={
    "person_id": PERSON_ID,
    "hours": 2,
    "minutes": 30,
    "description": "Weekend project work"
}, headers={"Authorization": f"Bearer {TOKEN}"})
test("Create extra hours - status 201", r.status_code == 201)
test("Extra hours has id", "id" in r.json())
EH_ID = r.json()["id"]
test("Extra hours correct hours", r.json().get("hours") == 2)

# Create extra hours for non-existent person
r = client.post("/api/extra-hours/", json={
    "person_id": 99999,
    "hours": 1,
    "minutes": 0
}, headers={"Authorization": f"Bearer {TOKEN}"})
test("Create hours invalid person - status 404", r.status_code == 404)

# List extra hours
r = client.get("/api/extra-hours/", headers={"Authorization": f"Bearer {TOKEN}"})
test("List extra hours - status 200", r.status_code == 200)
test("List extra hours is array", isinstance(r.json(), list))
test("List contains created record", any(eh["id"] == EH_ID for eh in r.json()))

# Get single extra hours record
r = client.get(f"/api/extra-hours/{EH_ID}", headers={"Authorization": f"Bearer {TOKEN}"})
test("Get extra hours by id - status 200", r.status_code == 200)
test("Get extra hours has person_id", r.json().get("person_id") == PERSON_ID)

# Update extra hours
r = client.put(f"/api/extra-hours/{EH_ID}", json={
    "hours": 3,
    "description": "Updated: Weekend project work + overtime"
}, headers={"Authorization": f"Bearer {TOKEN}"})
test("Update extra hours - status 200", r.status_code == 200)
test("Update hours changed", r.json().get("hours") == 3)
test("Update description changed", "Updated" in r.json().get("description", ""))

# Person hours summary
r = client.get(f"/api/extra-hours/persons/{PERSON_ID}/summary", headers={"Authorization": f"Bearer {TOKEN}"})
test("Person hours summary - status 200", r.status_code == 200)
test("Summary has total_hours", "total_hours" in r.json())
test("Summary has decimal_hours", "decimal_hours" in r.json())

# Delete extra hours
r = client.delete(f"/api/extra-hours/{EH_ID}", headers={"Authorization": f"Bearer {TOKEN}"})
test("Delete extra hours - status 204", r.status_code == 204)

# Verify deleted
r = client.get(f"/api/extra-hours/{EH_ID}", headers={"Authorization": f"Bearer {TOKEN}"})
test("Verify extra hours deleted - status 404", r.status_code == 404)

# Delete person (cascades remaining hours)
r = client.delete(f"/api/persons/{PERSON_ID}", headers={"Authorization": f"Bearer {TOKEN}"})
test("Delete person - status 204", r.status_code == 204)

# Verify person deleted
r = client.get(f"/api/persons/{PERSON_ID}", headers={"Authorization": f"Bearer {TOKEN}"})
test("Verify person deleted - status 404", r.status_code == 404)


# =============================================================================
# Summary
# =============================================================================
print(f"\n{'='*50}")
print(f"\U0001f4ca TEST RESULTS: {passed} passed, {failed} failed out of {passed + failed} total")
if failed == 0:
    print("\U0001f389 ALL TESTS PASSED!")
else:
    print(f"\u26a0\ufe0f  {failed} test(s) FAILED!")
print(f"{'='*50}")
