# Counter Backend — Extra Hours Management API

[English](#english) | [Polski](#polski)

## English

A REST API for tracking people's extra working hours. Built with **FastAPI**, **SQLAlchemy 2**, **Pydantic 2**, JWT authentication (`python-jose`) and bcrypt password hashing. SQLite is the default database. This repository contains the backend only.

### Features

- Administrator registration, login, profile and access-token renewal.
- Create, list, edit and delete people and their extra-hours records.
- Filter people by working status and records by person; paginate both lists.
- Summaries with normalized hours/minutes, decimal hours and record counts.
- Creator/editor tracking and timestamps; deleting a person deletes their hours.
- Interactive OpenAPI documentation and configurable CORS.

All active administrators share access to all people and records. Creator IDs provide attribution, **not per-user data isolation**.

### Quick start

Use Python 3.10 or newer; the regression suite was verified with Python 3.14. Run commands from the repository root.

```sh
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env
# Windows PowerShell: Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the generated value into `JWT_SECRET_KEY` in `.env`, then start:

```sh
python -m uvicorn main:app --reload
```

- API/health: <http://127.0.0.1:8000/>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

Tables are created at startup. The default `extra_hours.db` path is relative to the working directory. Startup does **not** migrate existing tables.

### Configuration

Settings are loaded from environment variables or `.env`; environment variables take precedence. Restart the application after changing settings. Never commit `.env` or a real signing secret.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./extra_hours.db` | SQLAlchemy connection URL |
| `JWT_SECRET_KEY` | Required, at least 32 characters | JWT signing secret; generate a random value |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access-token lifetime, positive integer |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh-token lifetime, positive integer |
| `ALLOW_REGISTRATION` | `true` | Enable public administrator registration |
| `CORS_ORIGINS` | localhost/127.0.0.1 on ports 5173, 4173, 3000 | JSON array of allowed frontend origins |
| `DEBUG` | `false` | Log SQL statements when enabled |
| `APP_NAME` | `Extra Hours Management API` | Application name |
| `APP_VERSION` | `1.0.0` | Application metadata version |

Example CORS setting:

```dotenv
CORS_ORIGINS=["https://frontend.example.com"]
```

Register the required administrators, then set `ALLOW_REGISTRATION=false` and restart before exposing the service publicly. While registration is enabled, anyone who can reach this endpoint can create an administrator with full data access.

### API

Register and log in using JSON bodies. For protected routes send `Authorization: Bearer <access_token>`. In Swagger UI, use **Authorize** and paste the access token.

| Method | Path | Access | Action |
| --- | --- | --- | --- |
| GET | `/` | Public | Application health |
| POST | `/api/auth/register` | Public, if enabled | Register an administrator |
| POST | `/api/auth/login` | Public | Receive access and refresh tokens |
| POST | `/api/auth/refresh` | Refresh token in JSON body | Receive new tokens |
| GET | `/api/auth/me` | Access token | Current administrator profile |
| GET, POST | `/api/persons/` | Access token | List/create people |
| GET, PUT, DELETE | `/api/persons/{person_id}` | Access token | Details with summary/update/delete |
| GET, POST | `/api/extra-hours/` | Access token | List/create hours records |
| GET, PUT, DELETE | `/api/extra-hours/{hours_id}` | Access token | Read/update/delete a record |
| GET | `/api/extra-hours/persons/{person_id}/summary` | Access token | Hours summary for one person |

List parameters: `skip=0`, `limit=100` (1–500). People accept `is_working=true/false`; hours accept `person_id`. People are ordered by ID; hours by date, creation time and ID descending.

`PUT` updates only supplied fields. Omit fields you want to preserve. Explicit `null` is rejected for person fields and record hours/minutes/date; `description: null` clears the description. Hours must be nonnegative, minutes must be 0–59 and dates use `YYYY-MM-DD` (default: current UTC day). Registration passwords require at least 6 characters and at most 72 UTF-8 bytes; multibyte characters count towards the byte limit.

Successful creation returns `201`, deletion `204`. Common errors: `401` invalid/missing token or credentials, `403` inactive account or disabled registration, `404` missing resource, `409` duplicate username/email, `422` invalid input.

### Example workflow

Examples use POSIX shell syntax; replace sample credentials, token and IDs with your own values.

```sh
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"Anna","surname":"Nowak","username":"admin","password":"replace-with-a-strong-password"}'

curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"replace-with-a-strong-password"}'

# Copy access_token from the login response.
TOKEN='paste-access-token-here'

curl -X POST http://127.0.0.1:8000/api/persons/ \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Jan","surname":"Kowalski","faculty":"IT"}'

# Replace person_id=1 with the ID returned above.
curl -X POST http://127.0.0.1:8000/api/extra-hours/ \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"person_id":1,"hours":2,"minutes":30,"description":"Project support","date":"2026-10-13"}'

curl http://127.0.0.1:8000/api/extra-hours/persons/1/summary \
  -H "Authorization: Bearer $TOKEN"

curl -X POST http://127.0.0.1:8000/api/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"paste-refresh-token-here"}'
```

For one 2h30m record, the summary contains `total_hours: 2`, `total_minutes: 30`, `decimal_hours: 2.5` and `total_records: 1`. `total_minutes` is the remaining minute component, not the entire duration expressed in minutes.

### Tests

```sh
python -m pip install -r requirements-dev.txt
python -m unittest -v
# Equivalent: python test_api.py
```

Tests run against a temporary SQLite database with independent credentials, create tables through the application lifespan, and reset data between cases. They cover authentication, invalid/expired tokens, password limits, CRUD, aggregation, validation, pagination, timestamps, CORS and cascade deletion. A failure produces a nonzero exit code. No running server is needed.

The installed Starlette version may emit a deprecation warning for its `httpx` test-client fallback; this does not prevent the tests from running.

### Project layout

```text
main.py                   # FastAPI app, lifespan, CORS and router registration
config.py                 # Environment settings
database.py              # Engine, sessions and table initialization
Models/models.py          # SQLAlchemy models
Models/schemas.py         # Request validation and response schemas
Routers/                  # Authentication, people and hours HTTP endpoints
Services/                 # Authentication and CRUD/business logic
dependencies.py           # Access-token validation and current administrator
test_api.py               # Isolated unittest regression suite
requirements.txt          # Runtime dependencies
requirements-dev.txt      # Runtime + test dependencies
.env.example              # Configuration template
```

### Operational notes and limitations

Use HTTPS, a private signing secret, appropriate CORS origins and `ALLOW_REGISTRATION=false` for a public deployment. `--reload` is for development. Back up the database before deployment; `create_all()` is not a migration system. Alternative SQLAlchemy databases require a separately installed driver and have not been verified by this test suite.

Refresh tokens are stateless: renewal issues new tokens but **does not invalidate the old refresh token**. There is no logout/revocation endpoint, password-reset implementation or login rate limiter. Deactivating an account prevents access and renewal. Changing the signing key invalidates all existing tokens.

Existing bcrypt hashes remain supported. Passwords previously silently truncated beyond 72 UTF-8 bytes must be replaced using an administrative procedure; oversized login passwords are now rejected. Existing timestamps are preserved; corrected timestamp generation applies to future writes. No database schema migration is required for these changes.

## Polski

REST API do ewidencji nadgodzin. Projekt wykorzystuje **FastAPI**, **SQLAlchemy 2**, **Pydantic 2**, uwierzytelnianie JWT (`python-jose`) oraz bcrypt do haszowania haseł. Domyślną bazą jest SQLite. Repozytorium zawiera wyłącznie backend.

### Funkcje

- Rejestracja administratorów, logowanie, profil i odświeżanie tokenów.
- Dodawanie, przeglądanie, edycja i usuwanie osób oraz wpisów nadgodzin.
- Filtrowanie osób według statusu zatrudnienia, wpisów według osoby i paginacja list.
- Podsumowania godzin, pozostałych minut, godzin dziesiętnych i liczby wpisów.
- Informacje o autorze, edytorze i czasie zmian; usunięcie osoby usuwa jej nadgodziny.
- Interaktywna dokumentacja OpenAPI i konfigurowalny CORS.

Każdy aktywny administrator ma dostęp do wszystkich osób i wpisów. Identyfikator autora służy do przypisania autorstwa, **nie do izolowania danych użytkowników**.

### Uruchomienie

Użyj Pythona 3.10 lub nowszego; testy regresyjne sprawdzono na Pythonie 3.14. Polecenia wykonuj w katalogu głównym repozytorium.

```sh
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env
# Windows PowerShell: Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Wklej wygenerowany sekret jako `JWT_SECRET_KEY` w `.env`, a następnie uruchom:

```sh
python -m uvicorn main:app --reload
```

- API/status: <http://127.0.0.1:8000/>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- Schemat OpenAPI: <http://127.0.0.1:8000/openapi.json>

Tabele powstają przy starcie aplikacji. Domyślna ścieżka `extra_hours.db` jest względna wobec katalogu uruchomienia. Start aplikacji **nie wykonuje migracji istniejących tabel**.

### Konfiguracja

Ustawienia pochodzą ze zmiennych środowiskowych lub `.env`; zmienne środowiskowe mają pierwszeństwo. Po zmianie konfiguracji uruchom aplikację ponownie. Nie dodawaj `.env` ani rzeczywistych sekretów do repozytorium.

| Zmienna | Wartość domyślna | Znaczenie |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./extra_hours.db` | Adres połączenia SQLAlchemy |
| `JWT_SECRET_KEY` | Wymagany, minimum 32 znaki | Sekret podpisu JWT; wygeneruj losową wartość |
| `JWT_ALGORITHM` | `HS256` | Algorytm podpisu JWT |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Ważność tokenu dostępu, dodatnia liczba minut |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Ważność tokenu odświeżania, dodatnia liczba dni |
| `ALLOW_REGISTRATION` | `true` | Publiczna rejestracja administratorów |
| `CORS_ORIGINS` | localhost/127.0.0.1, porty 5173, 4173, 3000 | Tablica JSON dozwolonych adresów frontendu |
| `DEBUG` | `false` | Włączenie logowania zapytań SQL |
| `APP_NAME` | `Extra Hours Management API` | Nazwa aplikacji |
| `APP_VERSION` | `1.0.0` | Wersja w metadanych aplikacji |

Przykład CORS:

```dotenv
CORS_ORIGINS=["https://frontend.example.com"]
```

Po utworzeniu potrzebnych kont ustaw `ALLOW_REGISTRATION=false` i zrestartuj aplikację przed publicznym udostępnieniem. Włączona rejestracja pozwala każdemu, kto ma dostęp do endpointu, utworzyć administratora z pełnym dostępem do danych.

### API i przykłady

Rejestracja i logowanie przyjmują JSON. Chronione endpointy wymagają nagłówka `Authorization: Bearer <access_token>`. W Swagger UI wybierz **Authorize** i wklej token dostępu. Przykłady `curl` w sekcji [Example workflow](#example-workflow) pokazują kompletny przebieg: rejestracja → logowanie → osoba → nadgodziny → podsumowanie → odświeżenie tokenów. Zastąp przykładowe dane, identyfikatory i tokeny własnymi wartościami.

| Metoda | Ścieżka | Dostęp | Działanie |
| --- | --- | --- | --- |
| GET | `/` | Publiczny | Status aplikacji |
| POST | `/api/auth/register` | Publiczny, jeśli włączony | Rejestracja administratora |
| POST | `/api/auth/login` | Publiczny | Token dostępu i odświeżania |
| POST | `/api/auth/refresh` | Token odświeżania w JSON | Wydanie nowych tokenów |
| GET | `/api/auth/me` | Token dostępu | Profil administratora |
| GET, POST | `/api/persons/` | Token dostępu | Lista/dodawanie osób |
| GET, PUT, DELETE | `/api/persons/{person_id}` | Token dostępu | Szczegóły z podsumowaniem/edycja/usuwanie |
| GET, POST | `/api/extra-hours/` | Token dostępu | Lista/dodawanie nadgodzin |
| GET, PUT, DELETE | `/api/extra-hours/{hours_id}` | Token dostępu | Odczyt/edycja/usuwanie wpisu |
| GET | `/api/extra-hours/persons/{person_id}/summary` | Token dostępu | Podsumowanie nadgodzin osoby |

Listy przyjmują `skip=0` i `limit=100` (1–500). Osoby można filtrować przez `is_working=true/false`, a nadgodziny przez `person_id`. Osoby są sortowane według ID, nadgodziny malejąco według daty, czasu utworzenia i ID.

`PUT` zmienia tylko przesłane pola. Pominięte pola zachowują wartość. Jawne `null` jest odrzucane dla pól osoby oraz godzin, minut i daty wpisu; `description: null` usuwa opis. Godziny muszą być nieujemne, minuty mieścić się w zakresie 0–59, a data mieć format `YYYY-MM-DD` (domyślnie bieżący dzień UTC). Hasło rejestracji musi mieć minimum 6 znaków i maksymalnie 72 bajty UTF-8; znaki wielobajtowe szybciej wyczerpują limit.

Dla wpisu 2 godziny 30 minut podsumowanie zwraca `total_hours: 2`, `total_minutes: 30`, `decimal_hours: 2.5`, `total_records: 1`. `total_minutes` oznacza pozostałe minuty po przeliczeniu pełnych godzin, a nie cały czas wyrażony w minutach.

Utworzenie zasobu zwraca `201`, usunięcie `204`. Typowe błędy: `401` nieprawidłowy/brakujący token lub dane logowania, `403` nieaktywne konto lub wyłączona rejestracja, `404` brak zasobu, `409` zajęty login/e-mail, `422` nieprawidłowe dane.

### Testy

```sh
python -m pip install -r requirements-dev.txt
python -m unittest -v
# Alternatywnie: python test_api.py
```

Testy używają tymczasowej bazy SQLite i własnych danych logowania. Tworzą tabele przez cykl życia aplikacji i zerują dane między przypadkami. Sprawdzają uwierzytelnianie, błędne/wygasłe tokeny, limity haseł, CRUD, sumowanie, walidację, paginację, znaczniki czasu, CORS i usuwanie powiązanych danych. Nie wymagają uruchomionego serwera. Niepowodzenie kończy polecenie niezerowym kodem wyjścia.

Zainstalowana wersja Starlette może wyświetlać ostrzeżenie o wycofywaniu obsługi `httpx` w kliencie testowym; nie blokuje to testów.

### Struktura projektu

| Plik/katalog | Odpowiedzialność |
| --- | --- |
| `main.py` | Aplikacja FastAPI, cykl życia, CORS i routery |
| `config.py` | Konfiguracja środowiskowa |
| `database.py` | Silnik bazy, sesje i tworzenie tabel |
| `Models/models.py` | Modele SQLAlchemy |
| `Models/schemas.py` | Walidacja żądań i schematy odpowiedzi |
| `Routers/` | Endpointy uwierzytelniania, osób i nadgodzin |
| `Services/` | Logika uwierzytelniania i operacji na danych |
| `dependencies.py` | Walidacja tokenu dostępu i bieżący administrator |
| `test_api.py` | Izolowane testy regresyjne unittest |
| `requirements.txt` | Zależności aplikacji |
| `requirements-dev.txt` | Zależności aplikacji i testów |
| `.env.example` | Szablon konfiguracji |

### Wdrożenie i ograniczenia

Publiczne wdrożenie powinno używać HTTPS, prywatnego sekretu JWT, właściwych adresów CORS i `ALLOW_REGISTRATION=false`. Opcja `--reload` służy do pracy lokalnej. Wykonaj kopię bazy przed wdrożeniem; `create_all()` nie zastępuje migracji. Inne bazy obsługiwane przez SQLAlchemy wymagają osobnego sterownika i nie zostały zweryfikowane tym zestawem testów.

Tokeny odświeżania są bezstanowe: wydanie nowych tokenów **nie unieważnia starego tokenu odświeżania**. Brakuje endpointu wylogowania/unieważniania tokenów, implementacji resetowania hasła oraz limitowania prób logowania. Dezaktywacja konta blokuje dostęp i odświeżanie. Zmiana sekretu podpisu unieważnia wszystkie dotychczasowe tokeny.

Istniejące hasze bcrypt pozostają obsługiwane. Hasła wcześniej automatycznie skracane powyżej 72 bajtów UTF-8 wymagają zmiany procedurą administracyjną; zbyt długie hasła logowania są teraz odrzucane. Istniejące znaczniki czasu pozostają zachowane; poprawione wyliczanie czasu dotyczy kolejnych zapisów. Te zmiany nie wymagają migracji schematu bazy.
