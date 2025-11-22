import time


def iso_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
