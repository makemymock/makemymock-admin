from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.stats.repository import StatsRepository
from modules.stats.schema import (
    OverviewResponse,
    SignupTrendPoint,
    TargetExamBreakdown,
)


class StatsService:
    def __init__(self, db: AsyncIOMotorDatabase, questions_db: AsyncIOMotorDatabase):
        self.repo = StatsRepository(db, questions_db)

    async def overview(self) -> OverviewResponse:
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        # Roll all counters into a single overview payload. We deliberately
        # fire these sequentially-but-cheap rather than in a gather() —
        # Motor pool size is plenty for the workload and sequential keeps
        # the code obvious.
        total_users = await self.repo.count_users()
        verified = await self.repo.count_verified_users()
        active = await self.repo.count_active_users()
        with_profile = await self.repo.count_users_with_profile()
        new_7 = await self.repo.count_users_since(seven_days_ago)
        new_30 = await self.repo.count_users_since(thirty_days_ago)

        total_sessions = await self.repo.count_sessions()
        completed_sessions = await self.repo.count_sessions("completed")
        pending_sessions = await self.repo.count_sessions("pending")
        sessions_7 = await self.repo.count_sessions_since(seven_days_ago)

        total_battles = await self.repo.count_battles()
        battles_7 = await self.repo.count_battles_since(seven_days_ago)

        total_questions = await self.repo.count_questions()

        trend_rows = await self.repo.signup_trend(days=30)
        trend = self._pad_trend(trend_rows, days=30)

        by_exam_rows = await self.repo.by_target_exam()
        by_exam = [
            TargetExamBreakdown(
                target_exam=str(row["_id"]) or "unspecified",
                count=int(row["count"]),
            )
            for row in by_exam_rows
        ]

        return OverviewResponse(
            total_users=total_users,
            verified_users=verified,
            active_users=active,
            users_with_profile=with_profile,
            new_users_last_7_days=new_7,
            new_users_last_30_days=new_30,
            total_mock_sessions=total_sessions,
            completed_mock_sessions=completed_sessions,
            pending_mock_sessions=pending_sessions,
            sessions_last_7_days=sessions_7,
            total_battles=total_battles,
            battles_last_7_days=battles_7,
            total_questions=total_questions,
            signup_trend_30d=trend,
            by_target_exam=by_exam,
        )

    @staticmethod
    def _pad_trend(rows: list[dict], days: int) -> list[SignupTrendPoint]:
        """Mongo only returns days that had signups. The chart wants the
        full window so the X-axis stays continuous."""
        counts = {row["_id"]: int(row["count"]) for row in rows}
        today = datetime.now(timezone.utc).date()
        out: list[SignupTrendPoint] = []
        for i in range(days - 1, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            out.append(SignupTrendPoint(date=d, count=counts.get(d, 0)))
        return out
