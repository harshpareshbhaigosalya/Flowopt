# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the FlowOpt AI Environment.

This environment simulates a remote team workflow for optimization training.
"""

from typing import Dict, List, Optional, Any
try:
    from openenv.core.env_server.types import Action, Observation
except ImportError:
    try:
        from openenv.core.models import Action, Observation
    except ImportError:
        # Final fallback for older or dev versions
        from openenv import Action, Observation
import json
from pydantic import Field, BaseModel, model_validator


class Task(BaseModel):
    """Represents a single work task."""
    id: int
    description: str
    deadline: int  # Steps remaining until deadline
    impact: int    # Impact score (1-5)
    required_skill: str


class TeamMember(BaseModel):
    """Represents a team member."""
    name: str
    skill: str
    workload: int  # Current number of assigned tasks


class FlowoptAction(Action):
    """Action for the FlowOpt environment."""
    priority_order: List[int] = Field(..., description="Ordered list of task IDs by priority")
    assignments: Dict[str, List[int]] = Field(..., description="Mapping of team member name to list of task IDs")

    @model_validator(mode='before')
    @classmethod
    def validate_json_strings(cls, data: Any) -> Any:
        """Attempt to parse strings as JSON for Web UI compatibility."""
        if isinstance(data, dict):
            for field_name in ['priority_order', 'assignments']:
                val = data.get(field_name)
                if isinstance(val, str) and val.strip():
                    try:
                        data[field_name] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        pass
        return data


class FlowoptObservation(Observation):
    """Observation from the FlowOpt environment."""
    tasks: List[Task] = Field(default_factory=list, description="List of available tasks")
    team: List[TeamMember] = Field(default_factory=list, description="Team member status")
    current_step: int = Field(default=0, description="Current step index")
    remaining_tasks: int = Field(default=0, description="Count of tasks yet to be completed")
    status_message: str = Field(default="", description="Status message explaining previous action outcome")
    score_breakdown: Optional[Dict[str, float]] = Field(default=None, description="Detailed reward breakdown")
