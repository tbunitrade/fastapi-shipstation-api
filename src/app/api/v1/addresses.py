import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.utils.shipstation_client import ShipStationClientError
from ...core.utils.shipstation_service import ShipStationService

router = APIRouter(tags=["addresses"])

def get_shipstation_service() -> ShipStationService:
    return ShipStationService()

TextQuery = Annotated[str, Query(min_length=1)]
AddressQuery = Annotated[str | None, Query(description="Optional JSON string")]
ServiceDep = Annotated[ShipStationService, Depends(get_shipstation_service)]

@router.get("/addresses/recognize")
async def recognize_address(
        text: TextQuery,
        service: ServiceDep,
        address: AddressQuery = None,
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
        # bad gateway
        raise HTTPException(status_code=502, detail=str(e))


