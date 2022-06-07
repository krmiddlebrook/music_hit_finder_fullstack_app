from fastapi import APIRouter

from app.api.api_v1.endpoints import items, login, users, tracks, utils, spotify

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(spotify.router, prefix="/spotify", tags=["spotify"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(tracks.router, prefix="/tracks", tags=["tracks"])
# TODO: Artists, Albums
