from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints

Subject = Annotated[str, StringConstraints(min_length=1, max_length=200)]
Body = Annotated[str, StringConstraints(min_length=1, max_length=200_000)]


class SendPromoRequest(BaseModel):
    subject: Subject
    body: Body
    recipients: list[EmailStr] = Field(..., min_length=1)
    # When true the body is wrapped in our branded HTML template; when
    # false it is rendered verbatim (admin supplies raw HTML).
    use_template: bool = True
    # When true any blank lines in `body` are preserved as paragraphs.
    # Only used when `use_template=True`.
    preserve_line_breaks: bool = True


class PerRecipientResult(BaseModel):
    email: EmailStr
    status: str  # "sent" | "failed"
    error: str | None = None


class SendPromoResponse(BaseModel):
    requested: int
    sent: int
    failed: int
    results: list[PerRecipientResult]


class PreviewRequest(BaseModel):
    subject: Subject
    body: Body
    use_template: bool = True
    preserve_line_breaks: bool = True


class PreviewResponse(BaseModel):
    subject: str
    html: str
