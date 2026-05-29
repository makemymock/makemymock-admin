"""Collection names + defaults for the admin contest module."""

# Primary DB collections (writes owned by this service).
CONTESTS_COLLECTION = "contests"

# Questions DB collection (read-only — picker source).
QUESTIONS_COLLECTION = "questions"

# Read-only collections in the primary DB. Owned by the Client backend's
# contest module, but the admin reads them for the participants view.
PARTICIPATIONS_COLLECTION = "contest_participations"

# Lobby opens this many seconds before start_time.
LOBBY_OPEN_SECONDS = 5 * 60

# Status values used in `contests.status`. Computed on read from the
# stored timestamps, so we never have to write a status update job.
STATUS_SCHEDULED = "scheduled"
STATUS_LIVE = "live"
STATUS_COMPLETED = "completed"

# Default marking scheme — admin can override per contest.
DEFAULT_MARKS_CORRECT = 4
DEFAULT_MARKS_WRONG = -1
DEFAULT_MARKS_UNATTEMPTED = 0

# Bounds on contest payloads.
MIN_DURATION_SECONDS = 60                # 1 minute
MAX_DURATION_SECONDS = 6 * 60 * 60       # 6 hours
MIN_QUESTIONS = 1
MAX_QUESTIONS = 200

# Default rules markdown. Frontend prefills this into the rules field on
# the create form. Tokens in `{...}` are substituted on the client side
# when the admin edits — server stores the raw markdown verbatim.
DEFAULT_RULES_MARKDOWN = """\
# Contest Rules & Regulations

Welcome. Please read the following carefully before you begin.

## Format
- **Total questions:** {question_count}
- **Duration:** {duration_minutes} minutes
- **Marking:** +{marks_correct} for a correct answer, {marks_wrong} for a wrong answer, {marks_unattempted} for unattempted.

## Honor code
- Work on your own. Sharing or seeking answers from anyone is a violation.
- Do not use external tools, AI assistants, books, notes, or other browser tabs.
- Any violation may result in your score being voided and contest entry being suspended.

## Test environment
- Use a stable internet connection. Reconnect quickly if you drop.
- **Do not refresh, close, or navigate away** during the contest. Your answers autosave, but a refresh can briefly disrupt your timer.
- The timer is server-authoritative — the clock keeps running even if your tab loses focus.

## Submission
- You may submit at any time before the timer ends.
- When the timer expires the contest is auto-submitted with whatever answers are saved.
- Once submitted, you cannot reopen the contest.

## Results
- The leaderboard ranks by **score**, breaking ties by **time taken** (faster wins).
- Per-question correctness and the worked solution review are available immediately after you submit.

Good luck.
"""
