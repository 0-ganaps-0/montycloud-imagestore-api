
# tests/test_response_serialization.py
import json
from decimal import Decimal
from src.common.response import json_response

def test_json_response_serializes_decimal():
    body = {"count": Decimal("10"), "ratio": Decimal("0.5")}
    r = json_response(200, body)
    assert r["statusCode"] == 200
    parsed = json.loads(r["body"])
    # integral -> int; fractional -> float
    assert isinstance(parsed["count"], int)
    assert isinstance(parsed["ratio"], float)
    assert parsed["count"] == 10
    assert parsed["ratio"] == 0.5
