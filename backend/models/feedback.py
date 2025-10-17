# User Feedback Models
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class FeedbackCreate(BaseModel):
    """Create feedback request"""

    message_id: str = Field(..., description="ID of the message being rated")
    rating: Literal["positive", "negative"] = Field(..., description="User rating")
    comment: Optional[str] = Field(None, description="Optional feedback comment")
    issue_type: Optional[Literal["incorrect", "incomplete", "irrelevant", "other"]] = (
        Field(None, description="Type of issue (for negative feedback)")
    )


class FeedbackResponse(BaseModel):
    """Feedback response"""

    id: str
    message_id: str
    user_id: Optional[str]
    rating: str
    comment: Optional[str]
    issue_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    """Feedback statistics"""

    total_feedback: int
    positive_count: int
    negative_count: int
    positive_rate: float
    common_issues: dict[str, int]
    time_period: str
