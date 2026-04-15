from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GraphValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    PENDING = "PENDING"
    ONGOING = "ONGOING"


class StateStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    EXECUTED = "EXECUTED"
    ERRORED = "ERRORED"
    NEXT_CREATED_ERROR = "NEXT_CREATED_ERROR"
    SUCCESS = "SUCCESS"
    PRUNED = "PRUNED"
    RETRY_CREATED = "RETRY_CREATED"


class RetryPolicy(BaseModel):
    max_retries: int = 0
    strategy: str = "EXPONENTIAL"
    backoff_factor_ms: int = 1000
    exponent: int = 2


class StoreConfig(BaseModel):
    required_keys: list[str] = Field(default_factory=list)
    default_values: dict[str, str] = Field(default_factory=dict)


class GraphNode(BaseModel):
    node_name: str
    namespace: str
    identifier: str
    inputs: dict[str, str] = Field(default_factory=dict)
    next_nodes: list[str] = Field(default_factory=list)
    unites: dict[str, Any] | None = None


class GraphTemplateReceipt(BaseModel):
    graph_name: str
    validation_status: GraphValidationStatus
    validation_errors: list[str] = Field(default_factory=list)


class TriggerReceipt(BaseModel):
    graph_name: str
    status: StateStatus
    run_id: str


class SignalReceipt(BaseModel):
    status: StateStatus
    enqueue_after: int
