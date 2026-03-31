"""Domain models for normalised Linear issues and labels."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Label(BaseModel):
    id: str
    name: str


class Issue(BaseModel):
    id: str
    identifier: str
    title: str
    description: str = ""
    state: str = ""
    labels: list[Label] = Field(default_factory=list)
