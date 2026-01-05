
# src/common/response.py
import json
from decimal import Decimal

def _json_default(o):
    # Convert Decimal to int (if integral) otherwise float
    if isinstance(o, Decimal):
        return int(o) if (o % 1) == 0 else float(o)
    # add other non-serializable types here if needed
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

def json_response(status_code: int, body: dict, headers: dict = None):
    h = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
    }
    if headers:
        h.update(headers)
    return {
        "statusCode": status_code,
        "headers": h,
        "body": json.dumps(body, default=_json_default),  # <-- use custom default
        "isBase64Encoded": False,
    }

def no_content():
    return {
        "statusCode": 204,
        "headers": {
            "Access-Control-Allow-Origin": "*",
        },
        "body": "",
        "isBase64Encoded": False,
    }
