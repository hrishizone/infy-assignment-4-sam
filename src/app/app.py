import json
import os
import logging
from typing import Dict, Any

import boto3
import mysql.connector
from mysql.connector import errorcode

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SECRET_ARN = os.environ["SECRET_ARN"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_NAME = os.environ["DB_NAME"]
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")
ALLOWED_HEADERS = os.environ.get("ALLOWED_HEADERS", "Authorization,customer_id")

sm = boto3.client("secretsmanager")

_conn = None 


def _cors_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    base = {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": ALLOWED_HEADERS,
    }
    if extra:
        base.update(extra)
    return base


def _get_db_credentials() -> Dict[str, str]:
    resp = sm.get_secret_value(SecretId=SECRET_ARN)
    secret_str = resp.get("SecretString") or "{}"
    creds = json.loads(secret_str)
    return {"username": creds["username"], "password": creds["password"]}


def _get_connection():
    global _conn
    if _conn and _conn.is_connected():
        return _conn

    creds = _get_db_credentials()
    _conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=creds["username"],
        password=creds["password"],
        database=DB_NAME,
        autocommit=False,
        connection_timeout=10,
    )
    return _conn


def _bootstrap_if_empty(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s",
            (DB_NAME,),
        )
        (table_count,) = cur.fetchone()
        if int(table_count) == 0:
            logger.info("No tables found in schema %s; bootstrapping...", DB_NAME)
            script_path = os.path.join(os.path.dirname(__file__), "database_script.sql")
            with open(script_path, "r", encoding="utf-8") as f:
                sql_text = f.read()
            for stmt in filter(None, (s.strip() for s in sql_text.split(";"))):
                if stmt:
                    cur.execute(stmt)
            conn.commit()
            logger.info("Bootstrap complete.")


def _get_lower_headers(event) -> Dict[str, str]:
    raw = event.get("headers") or {}
    return {str(k).lower(): v for k, v in raw.items()}


def _query_customer_aggregation(conn, customer_id: str) -> Dict[str, Any]:
    sql = """
        SELECT
            COUNT(t.transactions_id) AS tx_count,
            COALESCE(SUM(t.amount), 0) AS tx_sum
        FROM account a
        LEFT JOIN transactions t ON t.account_id = a.account_id
        WHERE a.customer_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (customer_id,))
        row = cur.fetchone()
        tx_count = int(row[0]) if row and row[0] is not None else 0
        tx_sum = float(row[1]) if row and row[1] is not None else 0.0
        return {"transaction_count": tx_count, "total_amount": tx_sum}


def lambda_handler(event, context):
    if event.get("httpMethod", "").upper() == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": ""
        }

    headers = _get_lower_headers(event)
    customer_id = headers.get("customer_id")
    if not customer_id:
        return {
            "statusCode": 400,
            "headers": _cors_headers(),
            "body": json.dumps({"message": "Missing required header: customer_id"})
        }

    try:
        conn = _get_connection()
        _bootstrap_if_empty(conn)
        result = _query_customer_aggregation(conn, customer_id)
        conn.commit()
        body = {
            "customer_id": customer_id,
            **result
        }
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps(body)
        }
    except mysql.connector.Error as e:
        logger.exception("MySQL error")
        code = e.errno or 500
        return {
            "statusCode": 500,
            "headers": _cors_headers(),
            "body": json.dumps({"message": "Database error", "code": code})
        }
    except Exception as e:
        logger.exception("Unhandled error")
        return {
            "statusCode": 500,
            "headers": _cors_headers(),
            "body": json.dumps({"message": "Internal server error"})
        }
