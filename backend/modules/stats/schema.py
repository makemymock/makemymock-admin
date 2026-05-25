from pydantic import BaseModel


class SignupTrendPoint(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class TargetExamBreakdown(BaseModel):
    target_exam: str
    count: int


class OverviewResponse(BaseModel):
    total_users: int
    verified_users: int
    active_users: int
    users_with_profile: int
    new_users_last_7_days: int
    new_users_last_30_days: int

    total_mock_sessions: int
    completed_mock_sessions: int
    pending_mock_sessions: int
    sessions_last_7_days: int

    total_battles: int
    battles_last_7_days: int

    total_questions: int

    signup_trend_30d: list[SignupTrendPoint]
    by_target_exam: list[TargetExamBreakdown]
