from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from data.models.job import Job
    from data.models.user import User


class Rating(SQLModel, table=True):

    job_id: int = Field(
        foreign_key="job.id", primary_key=True, nullable=False, index=True
    )
    user_id: int = Field(
        foreign_key="user.id", primary_key=True, nullable=False, index=True
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: func.now(), nullable=False
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: func.now(), nullable=False
    )
    user_rated: bool = Field(default=False, nullable=False)
    user_rating: Optional[float] = Field(default=None, nullable=True)
    user_rating_positives: Optional[str] = Field(default=None, nullable=True)
    user_rating_negatives: Optional[str] = Field(default=None, nullable=True)
    ai_processed: bool = Field(default=False, nullable=False, index=True)
    ai_longform_summary: Optional[str] = Field(default=None, nullable=True)
    ai_shortform_summary: Optional[str] = Field(default=None, nullable=True)
    ai_badge_summary: Optional[str] = Field(default=None, nullable=True)
    ai_expected_salary: Optional[str] = Field(default=None, nullable=True)
    ai_commute_time: Optional[str] = Field(default=None, nullable=True)
    ai_rated: bool = Field(default=False, nullable=False, index=True)
    ai_rating: Optional[float] = Field(default=None, nullable=True)
    ai_positives: Optional[str] = Field(default=None, nullable=True)
    ai_negatives: Optional[str] = Field(default=None, nullable=True)
    ai_skill_matches: Optional[str] = Field(default=None, nullable=True)
    ai_skill_discrepancies: Optional[str] = Field(default=None, nullable=True)
    ai_application_strategy: Optional[str] = Field(default=None, nullable=True)
    ai_difficulty_score: Optional[str] = Field(default=None, nullable=True)
    ai_cover_letter: Optional[str] = Field(default=None, nullable=True)

    job: "Job" = Relationship(back_populates="ratings")
    user: "User" = Relationship(back_populates="ratings")
