from fastapi import APIRouter

from core.dependencies import CurrentAdmin, DBDep, QuestionsDBDep
from modules.stats.schema import OverviewResponse
from modules.stats.service import StatsService

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Aggregate counters + 30-day signup trend for the dashboard",
)
async def overview(
    db: DBDep,
    questions_db: QuestionsDBDep,
    _: CurrentAdmin,
) -> OverviewResponse:
    return await StatsService(db, questions_db).overview()
