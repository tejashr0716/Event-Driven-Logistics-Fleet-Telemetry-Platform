from fastapi import APIRouter
from typing import List, Dict, Any
from ..services.database_service import db_service

router = APIRouter(prefix="", tags=["Fleet & Geofences"])

@router.get("/vehicles")
async def list_vehicles():
    vehicles = await db_service.get_active_vehicles()
    return {"count": len(vehicles), "vehicles": vehicles}

@router.get("/geofences")
async def list_geofences():
    fences = await db_service.get_active_geofences()
    return {"count": len(fences), "geofences": fences}
