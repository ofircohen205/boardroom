from fastapi import APIRouter

from backend.state.enums import Market

router = APIRouter(prefix="/api")


@router.get("/markets")
async def get_markets():
    return {m.value: m.name for m in Market}
