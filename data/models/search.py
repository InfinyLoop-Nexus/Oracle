from sqlmodel import Column, DateTime, SQLModel, Field, Relationship
from typing_extensions import Annotated
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import func

if TYPE_CHECKING:
    from data.models.user import User


def update_timestamp(context):
    return datetime.now()


class Search(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, default=datetime.now, nullable=False),
    )

    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        sa_column=Column(
            DateTime, default=datetime.now, onupdate=update_timestamp, nullable=False
        ),
    )

    user_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    job_title: str = Field(nullable=False)
    date_posted: str = Field(nullable=False)
    working_model: str = Field(nullable=False)
    location: str = Field(nullable=False)
    scraping_amount: int = Field(nullable=False)
    platform: str = Field(nullable=False)

    user: Optional["User"] = Relationship(back_populates="searches")
