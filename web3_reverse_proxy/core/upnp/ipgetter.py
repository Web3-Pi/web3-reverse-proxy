from functools import lru_cache
import whatismyip


@lru_cache(maxsize=None)
def my_public_ip() -> str | None:
    return whatismyip.whatismyip()
