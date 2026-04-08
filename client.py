# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""FlowOpt AI Environment Client."""

from typing import Dict, Any

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import FlowoptAction, FlowoptObservation, Task, TeamMember
except ImportError:
    from models import FlowoptAction, FlowoptObservation, Task, TeamMember


class FlowoptEnv(
    EnvClient[FlowoptAction, FlowoptObservation, State]
):
    """
    Client for the FlowOpt AI Environment.
    """

    def _step_payload(self, action: FlowoptAction) -> Dict:
        """
        Convert FlowoptAction to JSON payload for step message.
        """
        return action.dict()

    def _parse_result(self, payload: Dict) -> StepResult[FlowoptObservation]:
        """
        Parse server response into StepResult[FlowoptObservation].
        """
        obs_data = payload.get("observation", {})
        
        # Reconstruct Task and TeamMember objects if necessary (Pydantic does this automatically if using .parse_obj)
        # But we create FlowoptObservation directly here
        observation = FlowoptObservation(**obs_data)

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            metadata=payload.get("metadata", {})
        )
