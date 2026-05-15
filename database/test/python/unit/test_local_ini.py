"""Unit tests for database/config/local.ini — the CouchDB overlay applied by
the production image. CORS posture in particular is load-bearing for the
frontend SPA on port 4200 (dev) and for the in-network backend."""
from __future__ import annotations

import configparser
from pathlib import Path

import pytest


LOCAL_INI = Path("/app/database/config/local.ini")


@pytest.fixture(scope="module")
def parsed() -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    # CouchDB local.ini uses no value for some keys (e.g. enable_cors = true),
    # so the defaults are fine. allow_no_value handles bare keys cleanly.
    cp = configparser.ConfigParser(allow_no_value=True, strict=False)
    cp.read(LOCAL_INI)
    return cp


def test_cors_enabled(parsed: configparser.ConfigParser) -> None:
    assert parsed.get("httpd", "enable_cors").strip().lower() == "true"


def test_cors_credentials_allowed(parsed: configparser.ConfigParser) -> None:
    assert parsed.get("cors", "credentials").strip().lower() == "true"


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost",
        "http://localhost:4200",  # angular dev server
        "http://plc-datalink-rfc1006-database:5984",  # in-network backend access
    ],
)
def test_cors_origin_present(parsed: configparser.ConfigParser, origin: str) -> None:
    origins_raw = parsed.get("cors", "origins")
    origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
    assert origin in origins


@pytest.mark.parametrize("method", ["GET", "PUT", "POST", "DELETE"])
def test_cors_method_present(parsed: configparser.ConfigParser, method: str) -> None:
    methods_raw = parsed.get("cors", "methods")
    methods = [m.strip().upper() for m in methods_raw.split(",")]
    assert method in methods


def test_cors_headers_include_authorization(parsed: configparser.ConfigParser) -> None:
    headers_raw = parsed.get("cors", "headers")
    headers = [h.strip().lower() for h in headers_raw.split(",")]
    assert "authorization" in headers
    assert "content-type" in headers
