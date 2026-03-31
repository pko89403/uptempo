"""Protocol detection from Linear issue content.

Analyzes issue title, description, and labels to determine which schema
protocols are required, then maps each to a specialized agent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)

PROTOCOL_RULES: list[dict[str, Any]] = [
    {
        "protocol": "rest",
        "agent": "api-architect",
        "keywords": [
            "rest", "crud", "api", "endpoint", "resource",
            "http", "get", "post", "put", "delete", "patch",
        ],
        "confidence_boost_labels": ["api", "rest", "backend"],
    },
    {
        "protocol": "sse",
        "agent": "realtime-engineer",
        "keywords": [
            "sse", "server-sent", "event-stream", "eventsource",
            "streaming", "real-time push", "unidirectional",
        ],
        "confidence_boost_labels": ["realtime", "sse", "streaming"],
    },
    {
        "protocol": "websocket",
        "agent": "realtime-engineer",
        "keywords": [
            "websocket", "ws://", "wss://", "bidirectional",
            "chat", "real-time", "socket",
        ],
        "confidence_boost_labels": ["realtime", "websocket", "ws"],
    },
    {
        "protocol": "grpc",
        "agent": "grpc-engineer",
        "keywords": [
            "grpc", "protobuf", "proto", "rpc", "buf", "internal service",
        ],
        "confidence_boost_labels": ["grpc", "protobuf", "internal"],
    },
    {
        "protocol": "graphql",
        "agent": "graphql-architect",
        "keywords": [
            "graphql", "query", "mutation", "subscription",
            "sdl", "relay", "federation", "apollo",
        ],
        "confidence_boost_labels": ["graphql", "federation", "apollo"],
    },
    {
        "protocol": "kafka",
        "agent": "event-engineer",
        "keywords": [
            "kafka", "rabbitmq", "nats", "event", "queue", "pub/sub",
            "async", "domain event", "message broker", "cqrs", "event sourcing",
        ],
        "confidence_boost_labels": ["events", "kafka", "messaging", "async"],
    },
    {
        "protocol": "webhook",
        "agent": "integration-engineer",
        "keywords": [
            "webhook", "callback", "external", "saas",
            "integration", "hook", "notification",
        ],
        "confidence_boost_labels": ["webhook", "integration", "external"],
    },
    {
        "protocol": "mqtt",
        "agent": "realtime-engineer",
        "keywords": [
            "mqtt", "iot", "device", "telemetry", "sensor", "lwt", "qos",
        ],
        "confidence_boost_labels": ["iot", "mqtt", "device"],
    },
    {
        "protocol": "trpc",
        "agent": "trpc-engineer",
        "keywords": [
            "trpc", "zod", "typescript api", "type-safe",
            "fullstack", "next.js api",
        ],
        "confidence_boost_labels": ["trpc", "typescript", "fullstack"],
    },
]


class ProtocolMatch(BaseModel):
    """A detected protocol with its assigned agent and confidence score."""

    protocol: str
    agent: str
    confidence: float = Field(ge=0.0, le=1.0)
    matched_keywords: list[str] = Field(default_factory=list)


class ProtocolDetector:
    """Analyze Linear issues and detect which schema protocols are required."""

    def detect(self, issue: Issue) -> list[ProtocolMatch]:
        """Return matched protocols sorted by confidence (highest first).

        Scans the issue title, description, and labels against
        :data:`PROTOCOL_RULES`.  If no rules match, a default REST match
        with low confidence is returned.
        """
        text = f"{issue.title} {issue.description}".lower()
        label_names = {label.name.lower() for label in issue.labels}

        matches: list[ProtocolMatch] = []

        for rule in PROTOCOL_RULES:
            matched_keywords: list[str] = [
                kw for kw in rule["keywords"] if kw in text or kw in label_names
            ]
            if not matched_keywords:
                continue

            keyword_ratio = len(matched_keywords) / len(rule["keywords"])
            confidence = min(0.4 + keyword_ratio * 0.4, 0.8)

            boost_labels: list[str] = rule["confidence_boost_labels"]
            if label_names & set(boost_labels):
                confidence = min(confidence + 0.15, 1.0)

            matches.append(
                ProtocolMatch(
                    protocol=rule["protocol"],
                    agent=rule["agent"],
                    confidence=round(confidence, 2),
                    matched_keywords=matched_keywords,
                ),
            )

        if not matches:
            logger.info("no_protocol_match", issue_id=issue.identifier)
            matches.append(
                ProtocolMatch(
                    protocol="rest",
                    agent="api-architect",
                    confidence=0.3,
                ),
            )

        matches.sort(key=lambda m: m.confidence, reverse=True)

        logger.info(
            "protocols_detected",
            issue_id=issue.identifier,
            protocols=[m.protocol for m in matches],
        )
        return matches
