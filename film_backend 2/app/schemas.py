from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Film(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    year: int
    duration: int
    genres: List[str] = Field(default_factory=list)
    rating: float
    actors: List[str] = Field(default_factory=list)
    description: str
    similar: List[str] = Field(default_factory=list)


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


class AskResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)
    films: List[Film] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
