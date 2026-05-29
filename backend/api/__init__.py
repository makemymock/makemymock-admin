from fastapi import APIRouter

from modules.authentication.controller import router as auth_router
from modules.contest.controller import router as contest_router
from modules.promotional_email.controller import router as promo_email_router
from modules.questions.controller import router as questions_router
from modules.stats.controller import router as stats_router
from modules.users.controller import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(stats_router)
api_router.include_router(users_router)
api_router.include_router(promo_email_router)
api_router.include_router(questions_router)
api_router.include_router(contest_router)
