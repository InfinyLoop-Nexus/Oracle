from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from sqlalchemy.sql import func
from datetime import datetime


if TYPE_CHECKING:
    from data.models.user import User


class Search(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        default_factory=lambda: func.now(), nullable=False
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: func.now(), nullable=False
    )
    user_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    job_title: str = Field(nullable=False)
    date_posted: str = Field(nullable=False)
    working_model: str = Field(nullable=False)
    location: str = Field(nullable=False)
    scraping_amount: int = Field(nullable=False)
    platform: str = Field(nullable=False)

    user: Optional[list["User"]] = Relationship(back_populates="searches")
