"""Observability endpoints — read-only; gated by `CurrentAdmin`."""

from fastapi import APIRouter

from core.dependencies import CurrentAdmin, DBDep
from modules.observability.schema import InfraResponse, UsageResponse
from modules.observability.service import ObservabilityService

router = APIRouter(prefix="/observability", tags=["Observability"])


@router.get(
    "/usage",
    response_model=UsageResponse,
    summary="SolverX usage counters + per-model breakdown + 14-day sparkline (Mongo)",
)
async def usage(db: DBDep, _: CurrentAdmin) -> UsageResponse:
    return await ObservabilityService(db).usage()


@router.get(
    "/infra",
    response_model=InfraResponse,
    summary="Cloud Run infra metrics (Cloud Monitoring, 60s cached)",
)
async def infra(db: DBDep, _: CurrentAdmin) -> InfraResponse:
    return await ObservabilityService(db).infra()
