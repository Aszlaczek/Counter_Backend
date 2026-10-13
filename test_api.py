"""Isolated API regression tests: python -m unittest -v (or python test_api.py)."""
import datetime as dt
import os
import tempfile
import unittest
from unittest.mock import patch

# Configure an isolated database BEFORE importing the application. Never use .env data.
_test_directory = tempfile.TemporaryDirectory(prefix="counter-tests-")
os.environ.update(
    DATABASE_URL=f"sqlite:///{_test_directory.name}/test.db",
    JWT_SECRET_KEY="isolated-test-secret-not-for-production-use",
    DEBUG="false",
    ALLOW_REGISTRATION="true",
)

from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from Models.models import AdminUser, Person, ExtraHours
from Services.auth_service import settings, hash_password


# Own engine and dependency override protect application data even if another
# test runner imported database.py before this module.
engine = create_engine(f"sqlite:///{_test_directory.name}/test.db",
                       connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def test_db_session():
    with SessionLocal() as session:
        yield session


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password("test123456")

    def setUp(self):
        Base.metadata.drop_all(engine)
        app.dependency_overrides[get_db] = test_db_session
        self.addCleanup(app.dependency_overrides.pop, get_db)
        self.startup_patch = patch("main.init_db", lambda: Base.metadata.create_all(engine))
        self.startup_patch.start()
        self.addCleanup(self.startup_patch.stop)
        self.client = TestClient(app)
        self.client.__enter__()
        with SessionLocal() as db:
            db.add(AdminUser(name="Test", surname="Admin", username="tester",
                             hashed_password=self.password_hash))
            db.commit()
        response = self.client.post("/api/auth/login", json={
            "username": "tester", "password": "test123456"})
        self.assertEqual(response.status_code, 200)
        self.tokens = response.json()
        self.headers = {"Authorization": f"Bearer {self.tokens['access_token']}"}

    def tearDown(self):
        self.client.__exit__(None, None, None)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def person(self, **fields):
        response = self.client.post("/api/persons/", headers=self.headers,
                                    json={"name": "Jan", "surname": "Kowalski", **fields})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def hours(self, person_id, **fields):
        response = self.client.post("/api/extra-hours/", headers=self.headers,
                                    json={"person_id": person_id, **fields})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_health_and_openapi(self):
        self.assertEqual(self.client.get("/").json()["status"], "running")
        self.assertEqual(self.client.get("/openapi.json").status_code, 200)

    def test_registration_duplicates_and_password_limits(self):
        data = {"name": "New", "surname": "Admin", "username": "new-admin",
                "email": "test@example.com", "password": "ą" * 36}
        response = self.client.post("/api/auth/register", json=data)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertNotIn("hashed_password", response.json())
        self.assertEqual(self.client.post("/api/auth/register", json=data).status_code, 409)
        data["username"] = "other-admin"
        self.assertEqual(self.client.post("/api/auth/register", json=data).status_code, 409)
        data["password"] = "ą" * 37
        self.assertEqual(self.client.post("/api/auth/register", json=data).status_code, 422)
        self.assertEqual(self.client.post("/api/auth/login", json={
            "username": "new-admin", "password": "ą" * 36}).status_code, 200)
        self.assertEqual(self.client.post("/api/auth/login", json={
            "username": "new-admin", "password": "ą" * 37}).status_code, 401)

    def test_registration_can_be_disabled(self):
        with patch.object(settings, "allow_registration", False):
            response = self.client.post("/api/auth/register", json={
                "name": "New", "surname": "Admin", "username": "new-admin",
                "password": "test123456"})
        self.assertEqual(response.status_code, 403)

    def test_authentication_and_refresh(self):
        self.assertEqual(self.client.get("/api/auth/me", headers=self.headers).json()["username"], "tester")
        for path in ("/api/auth/me", "/api/persons/", "/api/extra-hours/"):
            self.assertEqual(self.client.get(path).status_code, 401)
            self.assertEqual(self.client.get(path, headers={"Authorization":
                f"Bearer {self.tokens['refresh_token']}"}).status_code, 401)
        self.assertEqual(self.client.post("/api/auth/login", json={
            "username": "tester", "password": "wrong"}).status_code, 401)
        response = self.client.post("/api/auth/refresh", json={
            "refresh_token": self.tokens["refresh_token"]})
        self.assertEqual(response.status_code, 200)
        for key in ("access_token", "refresh_token"):
            self.assertNotEqual(response.json()[key], self.tokens[key])
        self.assertEqual(self.client.post("/api/auth/refresh", json={
            "refresh_token": self.tokens["access_token"]}).status_code, 401)

    def test_invalid_expired_and_malformed_tokens(self):
        future = int(dt.datetime.now(dt.timezone.utc).timestamp()) + 3600
        for token_type in ("access", "refresh"):
            payloads = [
                {"sub": "not-a-number", "type": token_type, "exp": future},
                {"sub": "1", "type": token_type, "exp": 1},
                {"sub": "1", "type": token_type},
                {"sub": "0", "type": token_type, "exp": future},
                {"type": token_type, "exp": future},
            ]
            tokens = ["invalid-token"] + [jwt.encode(p, settings.jwt_secret_key,
                algorithm=settings.jwt_algorithm) for p in payloads]
            for token in tokens:
                with self.subTest(token_type=token_type, token=token):
                    if token_type == "access":
                        response = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
                    else:
                        response = self.client.post("/api/auth/refresh", json={"refresh_token": token})
                    self.assertEqual(response.status_code, 401, response.text)

    def test_inactive_account(self):
        with SessionLocal() as db:
            db.query(AdminUser).filter_by(username="tester").update({"is_active": False})
            db.commit()
        self.assertEqual(self.client.get("/api/auth/me", headers=self.headers).status_code, 403)
        self.assertEqual(self.client.post("/api/auth/refresh", json={
            "refresh_token": self.tokens["refresh_token"]}).status_code, 403)

    def test_crud_summaries_and_cascade(self):
        person = self.person()
        person_id = person["id"]
        summary_path = f"/api/extra-hours/persons/{person_id}/summary"
        self.assertEqual(self.client.get(summary_path, headers=self.headers).json()["total_records"], 0)
        record = self.hours(person_id, hours=2, minutes=45, description="Overtime", date="2026-10-12")
        self.hours(person_id, hours=1, minutes=45)
        summary = self.client.get(summary_path, headers=self.headers).json()
        self.assertEqual((summary["total_hours"], summary["total_minutes"], summary["decimal_hours"],
                          summary["total_records"]), (4, 30, 4.5, 2))
        detail = self.client.get(f"/api/persons/{person_id}", headers=self.headers).json()
        self.assertEqual((detail["total_extra_hours"], detail["extra_hours_count"]), (4.5, 2))
        response = self.client.put(f"/api/persons/{person_id}", headers=self.headers, json={"faculty": "IT"})
        self.assertEqual(response.json()["faculty"], "IT")
        path = f"/api/extra-hours/{record['id']}"
        response = self.client.put(path, headers=self.headers, json={"hours": 3, "description": None})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["hours"], 3)
        self.assertIsNone(response.json()["description"])
        self.assertEqual(self.client.delete(path, headers=self.headers).status_code, 204)
        self.assertEqual(self.client.get(path, headers=self.headers).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/persons/{person_id}", headers=self.headers).status_code, 204)
        self.assertEqual(self.client.get(summary_path, headers=self.headers).status_code, 404)
        with SessionLocal() as db:
            self.assertEqual(db.query(ExtraHours).count(), 0)

    def test_validation_and_missing_records(self):
        person = self.person()
        record = self.hours(person["id"])
        for field in ("name", "surname", "faculty", "is_working"):
            self.assertEqual(self.client.put(f"/api/persons/{person['id']}", headers=self.headers,
                                            json={field: None}).status_code, 422)
        for fields in ({"hours": None}, {"minutes": None}, {"date": None},
                       {"minutes": 60}, {"hours": -1}, {"date": "2026-02-30"}):
            self.assertEqual(self.client.put(f"/api/extra-hours/{record['id']}", headers=self.headers,
                                            json=fields).status_code, 422)
        self.assertEqual(self.client.post("/api/extra-hours/", headers=self.headers,
            json={"person_id": 99999}).status_code, 404)
        self.assertEqual(self.client.get("/api/persons/99999", headers=self.headers).status_code, 404)

    def test_pagination_and_filters(self):
        first = self.person(is_working=False)
        second = self.person()
        self.assertEqual(self.client.get("/api/persons/?is_working=false", headers=self.headers).json()[0]["id"], first["id"])
        self.assertEqual(self.client.get("/api/persons/?skip=1&limit=1", headers=self.headers).json()[0]["id"], second["id"])
        self.hours(first["id"])
        self.hours(second["id"])
        records = self.client.get(f"/api/extra-hours/?person_id={first['id']}", headers=self.headers).json()
        self.assertEqual([r["person_id"] for r in records], [first["id"]])
        for query in ("skip=-1", "limit=0", "limit=501"):
            self.assertEqual(self.client.get(f"/api/persons/?{query}", headers=self.headers).status_code, 422)

    def test_timestamps_are_evaluated_at_write(self):
        first = self.person()
        second = self.person()
        self.assertGreater(second["created_at"], first["created_at"])
        response = self.client.put(f"/api/persons/{first['id']}", headers=self.headers, json={"name": "Changed"})
        self.assertGreater(response.json()["updated_at"], first["updated_at"])
        self.assertEqual(response.json()["created_at"], first["created_at"])

    def test_cors_preflight(self):
        response = self.client.options("/api/persons/", headers={
            "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")


if __name__ == "__main__":
    unittest.main(verbosity=2)
