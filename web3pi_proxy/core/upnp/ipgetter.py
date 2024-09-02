from functools import lru_cache
from typing import Optional

import whatismyip


@lru_cache(maxsize=None)
def my_public_ip() -> Optional[str]:
    return whatismyip.whatismyip()
