
import base64
import hashlib
import uuid
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def gen_id() -> str:
    return str(uuid.uuid4())


def decode_b64(data: str) -> bytes:
    try:
        return base64.b64decode(data)
    except Exception as e:
        raise ValueError(f"Invalid base64: {e}")


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
