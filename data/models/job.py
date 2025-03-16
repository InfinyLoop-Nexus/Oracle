from sqlmodel import Field, SQLModel, Relationship, Column, DateTime
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from data.models.utils import update_timestamp

# Import only during type checking to avoid runtime circular imports
if TYPE_CHECKING:
    from data.models.rating import Rating


class Job(SQLModel, table=True):

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
    title: str = Field(nullable=False)
    description: str = Field(nullable=False)
    company: Optional[str] = Field(default=None, nullable=True)
    location: Optional[str] = Field(default=None, nullable=True)
    working_model: Optional[str] = Field(default=None, nullable=True)
    salary: Optional[str] = Field(default=None, nullable=True)
    experience_level: Optional[str] = Field(default=None, nullable=True)
    industry: Optional[str] = Field(default=None, nullable=True)
    responsibilities: Optional[str] = Field(default=None, nullable=True)
    requirements: Optional[str] = Field(default=None, nullable=True)
    ai_enhanced: bool = Field(default=False, nullable=False, index=True)
    applicants: Optional[str] = Field(default=None, nullable=True)
    posted_date: Optional[str] = Field(default=None, nullable=True)
    pretty_url: Optional[str] = Field(default=None, nullable=True)
    api_url: Optional[str] = Field(default=None, nullable=True)
    iid: Optional[str] = Field(default=None, nullable=True)

    # Relationships
    ratings: list["Rating"] = Relationship(back_populates="job")
