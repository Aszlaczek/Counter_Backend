"""Model exports loaded lazily so package discovery does not initialize the database."""
from importlib import import_module

_MODEL_NAMES = {"AdminUser", "Person", "ExtraHours"}
_SCHEMA_NAMES = {
    "AdminUserCreate", "AdminUserResponse", "TokenResponse", "PersonCreate",
    "PersonUpdate", "PersonResponse", "ExtraHoursCreate", "ExtraHoursUpdate",
    "ExtraHoursResponse",
}
__all__ = sorted(_MODEL_NAMES | _SCHEMA_NAMES)


def __getattr__(name):
    if name in _MODEL_NAMES:
        return getattr(import_module("Models.models"), name)
    if name in _SCHEMA_NAMES:
        return getattr(import_module("Models.schemas"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
