from __future__ import annotations

from typing import Any

from ..config import settings
from .shipstation_client import ShipStationClient

# Debug/quick access (можно оставить, не мешает)
api_key = settings.SHIPSTATION_API_KEY.get_secret_value()
base_url = settings.SHIPSTATION_BASE_URL
timeout = settings.SHIPSTATION_TIMEOUT_SECONDS
headers = settings.SHIPSTATION_HEADERS


class ShipStationService:
    def __init__(self, client: ShipStationClient | None = None) -> None:
        self._client = client or ShipStationClient()

    async def list_labels(self, *, page: int = 1, page_size: int = 50, **filters: Any) -> Any:
        params: dict[str, Any] = {"page": page, "pageSize": page_size, **filters}
        return (await self._client.get("/labels", params=params)).data

    async def recognize_address(self, *, text: str, address: dict[str, Any] | None = None ) -> Any:
        payload: dict[str, Any] = {"text": text}
        if address:
            payload["address"] = address

        # ShipEngine: PUT /v1/addresses/recognize
        resp = await self._client.put("/v1/addresses/recognize", json=payload)
        return resp.data