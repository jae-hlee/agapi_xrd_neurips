"""Anonymized REST client for the AGAPI-XRD endpoint.

The base URL is read exclusively from the AGAPI_XRD_ENDPOINT environment
variable to avoid hard-coding any identifying hostnames in the source.
"""
from __future__ import annotations

import os
from typing import Any

import httpx


DEFAULT_TIMEOUT = 300.0


class Client:
    """Minimal HTTP wrapper for the AGAPI-XRD endpoint.

    Endpoint URL is configured via env var. The auth key (if required) is
    passed as the APIKEY query parameter; the endpoint does not read
    Authorization headers.
    """

    def __init__(
        self,
        api_base: str | None = None,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_base = (api_base or os.environ.get("AGAPI_XRD_ENDPOINT", "")).rstrip("/")
        if not self.api_base:
            raise RuntimeError(
                "AGAPI_XRD_ENDPOINT environment variable is not set. "
                "See WEB_DEMO_URL.txt for the anonymous demo URL."
            )
        self.api_key = api_key or os.environ.get("AGAPI_XRD_KEY", "")
        self.timeout = timeout

    def request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        method: str = "GET",
    ) -> Any:
        params = dict(params or {})
        if self.api_key:
            params["APIKEY"] = self.api_key
        url = f"{self.api_base}/{path.lstrip('/')}"
        with httpx.Client(timeout=self.timeout) as session:
            if method == "GET":
                response = session.get(url, params=params)
            elif method == "POST":
                response = session.post(url, json=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        response.raise_for_status()
        ctype = response.headers.get("content-type", "")
        if "json" in ctype:
            return response.json()
        return response.text
