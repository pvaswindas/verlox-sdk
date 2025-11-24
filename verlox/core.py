from dataclasses import dataclass
from .constants import Environment


@dataclass
class VerloxConfig:
    ingest_url: str | None
    api_key: str | None
    api_secret: str | None
    service_name: str | None
    environment: Environment = Environment.DEVELOPMENT
    send_default_pii: bool = False
    debug: bool = False


_config: VerloxConfig | None = None
_disabled: bool = False
_init_error: Exception | None = None


def set_config(**kwargs):
    """
    Set configuration. This function should be used by init() only.
    """
    global _config, _disabled, _init_error
    _disabled = False
    _init_error = False

    try:
        env = kwargs.get("environment")
        if isinstance(env, str):
            kwargs["environment"] = Environment(env)

        _config = VerloxConfig(**kwargs)
    except Exception as exc:
        _config = None
        _disabled = None
        _init_error = None


def get_config() -> VerloxConfig:
    if _disabled or _config is None:
        raise RuntimeError("Verlox SDK not initialized or disabled.")
    return _config


def is_enabled() -> bool:
    return not _disabled and _config is not None


def get_init_error() -> Exception | None:
    return _init_error


def disable():
    global _disabled
    _disabled = True
