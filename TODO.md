# Implementation TODO: Admin Extra Hours Management API

## Phase 1: Foundation

- [x] 1. Create `config.py` — Settings (DB URL, JWT config)
- [x] 2. Create `database.py` — SQLAlchemy engine, session, Base
- [x] 3. Update `Models/models.py` — SQLAlchemy ORM models (AdminUser, Person, ExtraHours)
- [x] 4. Create `Models/schemas.py` — Pydantic request/response schemas
- [x] 5. Create `dependencies.py` — get_db(), get_current_admin() dependencies

## Phase 2: Business Logic (Services)

- [x] 6. Create `Services/auth_service.py` — Registration, login, JWT tokens
- [x] 7. Create `Services/person_service.py` — Person CRUD logic
- [x] 8. Create `Services/extra_hours_service.py` — Extra hours CRUD logic

## Phase 3: API Endpoints (Routers)

- [x] 9. Create `Routers/auth.py` — /api/auth/register, /login, /me
- [x] 10. Create `Routers/persons.py` — /api/persons CRUD
- [x] 11. Create `Routers/extra_hours.py` — /api/extra-hours CRUD

## Phase 4: Wiring & Testing

- [x] 12. Update `main.py` — Include routers, startup events
- [x] 13. Update `requirements.txt` — Add new dependencies
- [x] 14. Install dependencies & test the app

## Phase 5: Verification

- [x] 15. Create **init**.py files for packages
- [x] 16. Run the server and verify endpoints via /docs
- [x] 17. All 47 API tests PASSED

## Project Structure

```
Counter_Backend/
├── main.py                     # FastAPI app with startup event
├── config.py                   # Settings (DB URL, JWT secret, etc.)
├── database.py                 # SQLAlchemy engine + session + Base
├── dependencies.py             # get_db(), get_current_admin()
├── requirements.txt            # Project dependencies
├── test_api.py                 # Comprehensive test suite (47 tests)
├── TODO.md                     # This tracker
├── Models/
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy ORM models
│   └── schemas.py              # Pydantic request/response schemas
├── Routers/
│   ├── __init__.py
│   ├── auth.py                 # Auth endpoints
│   ├── persons.py              # Person CRUD endpoints
│   └── extra_hours.py          # Extra hours CRUD endpoints
└── Services/
    ├── __init__.py
    ├── auth_service.py          # Auth business logic
    ├── person_service.py        # Person business logic
    └── extra_hours_service.py   # Extra hours business logic
```
