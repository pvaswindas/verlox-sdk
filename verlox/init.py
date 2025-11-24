from .core import set_config, is_enabled
from .capture import setup_global_exception_hooks
from .integrations import instrument_asyncio_tasks
from .sender import start_sender_loop
from .internal_logger import enable_file_debug, disable_debug
from .constants import Environment
from .config_resolver import fetch_ingest_url


def init(
    api_key: str | None = None,
    api_secret: str | None = None,
    service_name: str | None = None,
    environment: Environment | None = None,
    send_default_pii: bool = False,
    debug: bool = False,
):
    try:
        ingest_url = fetch_ingest_url()
        set_config(
            ingest_url=ingest_url,
            api_key=api_key,
            api_secret=api_secret,
            service_name=service_name,
            environment=environment,
            send_default_pii=send_default_pii,
            debug=debug,
        )
    except Exception:
        pass

    try:
        if debug:
            enable_file_debug()
        else:
            disable_debug()
    except Exception:
        pass

    try:
        if not is_enabled():
            return
    except Exception:
        pass

    try:
        setup_global_exception_hooks()
    except Exception:
        pass

    try:
        instrument_asyncio_tasks()
    except Exception:
        pass

    try:
        start_sender_loop()
    except Exception:
        pass
