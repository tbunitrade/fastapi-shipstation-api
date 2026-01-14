from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import logging
import httpx

from ..config import settings
logger = logging.getLogger(__name__)

class ShipStationClientError(Exception):
    """Base common error from ShipStation Client"""

class ShipStationAuthError(ShipStationClientError):
    pass

class ShipStationRateLimitError(ShipStationClientError):
    pass

class ShipStationRequestError(ShipStationClientError):
    pass

@dataclass(frozen=True)
class ShipStationResponse:
    status_code: int
    data: Any

class ShipStationClient:
    """
    Minimal async http client for API testing,
    we are using real sandbox key.
    Prepared api-key header for settings.SHIPSTATION_HEADERS.
    """

    def __init__(self) -> None:
        self._base_url = settings.SHIPSTATION_BASE_URL.rstrip("/")
        self._timeout = float(settings.SHIPSTATION_TIMEOUT_SECONDS)
        self._headers = dict(settings.SHIPSTATION_HEADERS)

        # additional log support
        self._headers.setdefault("User-Agent", f"{settings.APP_NAME}/{settings.APP_VERSION or '0.1'}")

    async def request(
            self,
            method: str,
            path: str,
            *,
            params: dict[str, Any] | None = None,
            json: dict[str, Any] | None = None,
    ) -> ShipStationResponse:
        url = f"{self._base_url}/{path.lstrip('/')}"

        safe_headers = dict(self._headers)
        for k in ("API-Key", "api-key", "Authorization"):
            if k in safe_headers:
                safe_headers[k] = "***redacted***"

        logger.info("ShipStation request: %s %s", method, url)
        if params is not None:
            logger.info("ShipStation params: %s", params)
        if json is not None:
            logger.info("ShipStation json: %s", json)
        logger.debug("ShipStation headers: %s", safe_headers)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.request(
                    method,
                    url,
                    headers=self._headers,
                    params=params,
                    json=json,
                )
        except httpx.TimeoutException as e:
            logger.exception("ShipStation timeout: %s %s", method, url)
            raise ShipStationRequestError(f"ShipStation timeout {url}") from e
        except httpx.HTTPError as e:
            logger.exception("ShipStation HTTP error: %s %s", method, url)
            raise ShipStationRequestError(f"ShipStation HTTP classic error call {url} : {e}") from e

        logger.info("ShipStation response: %s %s -> %s", method, url, resp.status_code)
        logger.debug("ShipStation response body (first 500): %s", resp.text[:500])

        if resp.status_code in (401, 403):
            raise ShipStationAuthError(f"ShipStation auth error: {resp.status_code}")
        if resp.status_code == 429:
            raise ShipStationRateLimitError("ShipStation rate limited (429)")
        if resp.status_code >= 400:
            raise ShipStationRequestError(f"ShipStation error {resp.status_code} : {resp.text[:500]}")

        income = resp.headers.get("content-type", "")
        if "application/json" in income:
            data: Any = resp.json()
        else:
            data = resp.text

        return ShipStationResponse(status_code=resp.status_code, data=data)

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> ShipStationResponse:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, *, json: dict[str, Any] | None = None) -> ShipStationResponse:
        return await self.request("POST", path, json=json)

    async def put(self, path: str, *, json: dict[str, Any] | None = None) -> ShipStationResponse:
        return await self.request("PUT", path, json=json)