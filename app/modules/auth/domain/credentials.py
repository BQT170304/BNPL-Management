from __future__ import annotations

import hmac


def verify(username: str, password: str, expected_user: str, expected_pass: str) -> bool:
    """Constant-time check of both credential fields."""
    user_ok = hmac.compare_digest(username, expected_user)
    pass_ok = hmac.compare_digest(password, expected_pass)
    return user_ok and pass_ok
