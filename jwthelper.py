import datetime
from typing import Any, Dict, Optional

import jwt

from configuration import JWT_SECRET, JWT_ALG, JWT_EXPIRES_MIN


def create_jwt(payload: Dict[str, Any]) -> str:
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXPIRES_MIN)
    to_encode = {**payload, "exp": exp}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        return None


