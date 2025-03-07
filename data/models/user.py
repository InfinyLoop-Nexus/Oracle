from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from data.models.rating import Rating
    from data.models.search import Search

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.sql import func
from sqlalchemy import Column, String


class User(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[str] = Field(
        default_factory=lambda: func.now(),
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: Optional[str] = Field(
        default_factory=lambda: func.now(),
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    password_hash: str
    tokens_spent_lifetime: float = Field(default=0)
    tokens_spent_current_month: float = Field(default=0)
    tokens_spent_counter: float = Field(default=0)
    home_address: str = Field(default="")
    self_assessment: str = Field(default="", sa_column=Column(String))
    job_prototype: str = Field(default="", sa_column=Column(String))
    job_preferences: str = Field(default="", sa_column=Column(String))
    job_dislikes: str = Field(default="", sa_column=Column(String))
    desired_compensation: str = Field(default="")
    cover_letter: str = Field(default="", sa_column=Column(String))
    resume: str = Field(default="", sa_column=Column(String))
    encoded_openai_api_key: str = Field(default="")

    # OPTIONS
    duplicate_behavior: str = Field(default="skip_duplicates")

    # UTILS
    admin: bool = Field(default=False)

    # RELATIONSHIPS
    ratings: list["Rating"] = Relationship(back_populates="user")
    searches: list["Search"] = Relationship(back_populates="user")
