from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from ..config import settings

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
        self._base_url  = settings.SHIPSTATION_BASE_URL.rstrip("/")
        self._timeout   = float(settings.SHIPSTATION_TIMEOUT_SECONDS)
        self._headers   = dict(settings.SHIPSTATION_HEADERS)

        #additional log support
        self._headers.setdefault("User-Agent", f"{settings.APP_NAME}/{settings.APP_VERSION or '0.1'}")

    async def request(
            self,
            method:     str,
            path:       str,
            *,
            params:     dict[str, Any] | None = None,
            json:       dict[str, Any] | None = None,
    ) -> ShipStationResponse:
        url = f"{self._base_url}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.request(method, url, headers=self._headers, params=params, json=json)
        except httpx.TimeoutException as e:
            raise ShipStationRequestError(f"ShipStation timeout {url}") from e
        except httpx.HTTPError as e:
            raise ShipStationRequestError(f"ShipStation HTTP classic error call {url} : {e}") from e

        # status code
        if resp.status_code in (401,403):
            raise ShipStationAuthError(f"ShipStation auth error: {resp.status_code}")
        if resp.status_code == 429:
            raise ShipStationRateLimitError(f"ShipStation rate limited (429)")
        if resp.status_code >= 400:
            raise ShipStationRequestError(f"ShipStation error {resp.status_code} : {resp.text[:500]}")

        #accept any answer, default should be JSON
        data: Any

        income = resp.headers.get("content-type", "")
        if "application/json" in income:
            data = resp.json()
        else:
            data = resp.text

        return ShipStationResponse(status_code=resp.status_code, data=data)

    async  def get(self, path: str, *, params: dict[str, Any] | None = None) -> ShipStationResponse:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, *, json: dict[str, Any] | None = None) -> ShipStationResponse:
        return await self.request("POST", path, json=json)

    async def put(self, path: str, *, json: dict[str, Any] | None = None) -> ShipStationResponse:
        return  await self.request("PUT", path, json=json)

