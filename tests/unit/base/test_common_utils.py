
# tests/test_common_utils.py
import pytest
import base64
import uuid

from src.common.utils import now_iso, gen_id, decode_b64, sha256_hex

def test_gen_id_is_uuid():
    val = gen_id()
    uuid.UUID(val)  # raises if invalid

def test_now_iso_format():
    val = now_iso()
    assert "T" in val and val.endswith("+00:00")

def test_decode_b64_success():
    b = decode_b64(base64.b64encode(b"abc").decode())
    assert b == b"abc"

def test_decode_b64_invalid():
    with pytest.raises(ValueError):
        decode_b64("not-b64")

def test_sha256_hex():
    assert sha256_hex(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
