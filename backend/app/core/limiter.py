"""
CampusFlow — Rate Limiting Configuration.

Provides the slowapi Limiter instance using remote IP address keying.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Default limiter keyed by client remote IP address
limiter = Limiter(key_func=get_remote_address)
