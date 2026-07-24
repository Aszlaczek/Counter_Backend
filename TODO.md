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

- [x] 9. Create `Routers/auth.py` — /api/auth/register, /login, /refresh, /me
- [x] 10. Create `Routers/persons.py` — /api/persons CRUD
- [x] 11. Create `Routers/extra_hours.py` — /api/extra-hours CRUD

## Phase 4: Wiring & Testing

- [x] 12. Update `main.py` — Include routers, startup events
- [x] 13. Update `requirements.txt` — Add new dependencies
- [x] 14. Install dependencies & test the app

## Phase 5: Refresh Token Feature

- [x] 15. Add `jwt_refresh_token_expire_days` to config
- [x] 16. Update TokenResponse schema with refresh_token field
- [x] 17. Add `verify_refresh_token()` to auth_service
- [x] 18. Wire refresh token into /login response
- [x] 19. Rewrite /refresh endpoint to accept refresh token from body
- [x] 20. Update tests with refresh token coverage
