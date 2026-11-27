import os
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

def normalize_database_url(url: str) -> str:
    """
    Safely normalizes PostgreSQL connection URLs for SQLAlchemy 2.0 and Psycopg 3.
    Ensures 'postgresql+psycopg://' scheme and 'sslmode=require' for Neon.
    """
    if not url or not isinstance(url, str):
        return ""

    url = url.strip()

    # Replace legacy or unadorned scheme
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    # Parse and ensure sslmode=require
    parsed = urlparse(url)
    query_params = dict(parse_qsl(parsed.query))
    if "sslmode" not in query_params:
        query_params["sslmode"] = "require"

    new_query = urlencode(query_params)
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    return normalized

def redact_database_url(url: str) -> str:
    """
    Redacts password and sensitive user info from connection strings for safe logging.
    Example: postgresql+psycopg://user:****@ep-xyz.neon.tech/neondb?sslmode=require
    """
    if not url:
        return "[NOT_CONFIGURED]"
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc
        if "@" in netloc:
            auth, host = netloc.split("@", 1)
            if ":" in auth:
                username, _ = auth.split(":", 1)
                safe_auth = f"{username}:****"
            else:
                safe_auth = "****"
            netloc = f"{safe_auth}@{host}"
        return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    except Exception:
        return "[REDACTED_URL]"

