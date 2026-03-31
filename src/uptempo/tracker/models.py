"""Domain models for normalised Linear issues and labels."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Label(BaseModel):
    id: str
    name: str

    @classmethod
    def from_linear_node(cls, node: dict[str, Any]) -> Label:
        """Build a label from a Linear GraphQL node payload."""
        return cls(id=str(node["id"]), name=str(node["name"]))


class Issue(BaseModel):
    id: str
    identifier: str
    title: str
    description: str = ""
    url: str = ""
    state: str = ""
    labels: list[Label] = Field(default_factory=list)

    @classmethod
    def from_linear_node(cls, node: dict[str, Any]) -> Issue:
        """Build an issue from a Linear GraphQL node payload."""
        state_node = node.get("state")
        state_name = state_node.get("name", "") if isinstance(state_node, dict) else ""

        labels_node = node.get("labels", {})
        raw_label_nodes: list[Any]
        if isinstance(labels_node, dict):
            nested_nodes = labels_node.get("nodes", [])
            raw_label_nodes = nested_nodes if isinstance(nested_nodes, list) else []
        elif isinstance(labels_node, list):
            raw_label_nodes = labels_node
        else:
            raw_label_nodes = []

        labels = [
            Label.from_linear_node(label_node)
            for label_node in raw_label_nodes
            if isinstance(label_node, dict)
        ]

        return cls(
            id=str(node["id"]),
            identifier=str(node["identifier"]),
            title=str(node["title"]),
            description=str(node.get("description") or ""),
            url=str(node.get("url") or ""),
            state=state_name,
            labels=labels,
        )
