import os
import json
from typing import Dict, Any

EXPECTED = os.environ.get("EXPECTED_TOKEN", "")

def _generate_policy(principal_id: str, effect: str, method_arn: str) -> Dict[str, Any]:
    return {
        "principalId": principal_id or "caller",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": method_arn,
                }
            ],
        },
        "context": {
            "authorized": str(effect == "Allow").lower()
        }
    }

def handler(event, context):
    token = event.get("authorizationToken") or ""
    method_arn = event.get("methodArn")

    if not token or token != EXPECTED:
        return _generate_policy("user", "Deny", method_arn)

    return _generate_policy("user", "Allow", method_arn)
