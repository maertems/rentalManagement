from fastapi import APIRouter
from app.api.v1 import (
    auth,
    me,
    users,
    owners,
    places,
    placesUnits,
    placesUnitsRooms,
    tenants,
    rents,
    rentsFees,
    rentReceipts,
    rentReceiptsDetails,
    dashboard,
    withdraw,
    params,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(users.router)
api_router.include_router(owners.router)
api_router.include_router(places.router)
api_router.include_router(placesUnits.router)
api_router.include_router(placesUnitsRooms.router)
api_router.include_router(tenants.router)
api_router.include_router(rents.router)
api_router.include_router(rentsFees.router)
api_router.include_router(rentReceipts.router)
api_router.include_router(rentReceiptsDetails.router)
api_router.include_router(dashboard.router)
api_router.include_router(withdraw.router)
api_router.include_router(params.router)
