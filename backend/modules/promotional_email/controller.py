from fastapi import APIRouter, status

from core.dependencies import CurrentAdmin
from modules.promotional_email.schema import (
    PreviewRequest,
    PreviewResponse,
    SendPromoRequest,
    SendPromoResponse,
)
from modules.promotional_email.service import PromoEmailService

router = APIRouter(prefix="/promo-emails", tags=["Promotional Email"])


@router.post(
    "/preview",
    response_model=PreviewResponse,
    summary="Render the email body to HTML without sending",
)
async def preview(payload: PreviewRequest, _: CurrentAdmin) -> PreviewResponse:
    return await PromoEmailService().preview(payload)


@router.post(
    "/send",
    response_model=SendPromoResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a promotional email to a list of recipients",
)
async def send(payload: SendPromoRequest, _: CurrentAdmin) -> SendPromoResponse:
    return await PromoEmailService().send(payload)
