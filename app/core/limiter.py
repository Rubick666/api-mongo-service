import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def get_test_aware_limit():
    if os.getenv("TESTING") == "1":
        return False
    return True


limiter = Limiter(
    key_func=get_remote_address,
    enabled=get_test_aware_limit(),
)