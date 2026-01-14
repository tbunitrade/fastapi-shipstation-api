import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ...core.utils.shipstation_client import ShipStationClientError
from ...core.utils.shipstation_service import ShipStationService

router = APIRouter(tags=["addresses"])

def get_shipstation_service() -> ShipStationService:
    return ShipStationService()

@router.get("/addresses/recognize")
async def recognize_address(
        request: Request,
        text: Annotated[str, Query(min_length=1, description="Unstructured text to parse")],
        address: Annotated[
            str | None,
            Query(
                default=None,
                desctiption='Get Adress Fields {city_location" : "Austin"}'
            ),
        ] = None,
        service: Annotated[ShipStationService, Depends(get_shipstation_service)] = None,
) -> Any:
    address_obj: dict[str, Any] | None = None
    if address:
        try:
            address_obj = json.loads(address)
            if not isinstance(address_obj, dict):
                raise ValueError("Json expected")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid 'adress' JSON: {e}")
    try:
        return await service.recognize_address(text=text, address=address_obj)
    except ShipStationClientError as e:
        # bad gatewau
        raise HTTPException(status_code=502, detail=str(e))


