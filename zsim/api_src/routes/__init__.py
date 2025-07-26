from fastapi import APIRouter

from . import session_op, character_config, enemy_config, apl

router = APIRouter()

router.include_router(session_op.router, tags=["Session"])
router.include_router(character_config.router, tags=["Character"])
router.include_router(enemy_config.router, tags=["Enemy"])
router.include_router(apl.router, tags=["APL"])
