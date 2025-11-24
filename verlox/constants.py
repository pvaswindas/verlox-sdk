from enum import StrEnum


class Environment(StrEnum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    SANDBOX = "sandbox"
    PRODUCTION = "production"


# DSN server (unchanging)
DSN_ENDPOINT = "https://dsn.verlox.dev/python"
DSN_TIMEOUT = 3  # seconds

# Ingest defaults
DEFAULT_INGEST_TIMEOUT = 5  # seconds

# Header names
HEADER_VERLOX_KEY = "X-Verlox-Key"
HEADER_VERLOX_SIGNATURE = "X-Verlox-Signature"

# Signature defaults
SIGNATURE_ALGO = "sha256"

# JSON settings
JSON_SEPARATORS = (",", ":")
JSON_SORT_KEYS = True

# Max queue size for events
QUEUE_MAX_SIZE = 1000


# Sender retry settings
MAX_RETRY_ATTEMPTS = 5
MAX_BACKOFF_SECONDS = 30


# SDK metadata
SDK_NAME = "verlox"
SDK_VERSION = "0.1.0"
