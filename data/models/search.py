from sqlmodel import SQLModel, Field, Relationship
from pydantic import field_validator, BeforeValidator
from typing_extensions import Annotated
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from data.models.user import User


def parse_datetime(value):
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value

class Search(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Annotated[Optional[datetime], BeforeValidator(parse_datetime)] = Field(
        default_factory=datetime.now,
        nullable=False,
    )
    updated_at: Optional[datetime] = Field(default_factory=datetime.now, nullable=False)
    user_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    job_title: str = Field(nullable=False)
    date_posted: str = Field(nullable=False)
    working_model: str = Field(nullable=False)
    location: str = Field(nullable=False)
    scraping_amount: int = Field(nullable=False)
    platform: str = Field(nullable=False)

    user: Optional[list["User"]] = Relationship(back_populates="searches")

    @staticmethod
    def parse(json: str) -> "Search":
        validated: Search = Search.model_validate_json(json)
        validated.created_at = parse_datetime(validated.created_at)
        validated.updated_at = parse_datetime(validated.created_at)
        return validated

    @classmethod
    @field_validator("created_at", mode="before")
    def parse_timestamp(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)  # parse ISO 8601 string to datetime
        return value
