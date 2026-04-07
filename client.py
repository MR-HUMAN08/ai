# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Redteampentestlab Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import RedTeamAction, RedTeamObservation


class RedteampentestlabEnv(
    EnvClient[RedTeamAction, RedTeamObservation, State]
):
    """
    Client for the Redteampentestlab Environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    Example:
        >>> # Connect to a running server
        >>> with RedteampentestlabEnv(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(result.observation.target_ip)
        ...
        ...     result = client.step(RedTeamAction(action="scan"))
        ...     print(result.observation.output)

    Example with Docker:
        >>> # Automatically start container and connect
        >>> client = RedteampentestlabEnv.from_docker_image("redteampentestlab-env:latest")
        >>> try:
        ...     result = client.reset()
        ...     result = client.step(RedTeamAction(action="enumerate"))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: RedTeamAction) -> Dict:
        """
        Convert RedTeamAction to JSON payload for step message.

        Args:
            action: RedTeamAction instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        return {
            "action": action.action,
        }

    def _parse_result(self, payload: Dict) -> StepResult[RedTeamObservation]:
        """
        Parse server response into StepResult[RedTeamObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with RedTeamObservation
        """
        obs_data = payload.get("observation", {})
        observation = RedTeamObservation(
            target_ip=obs_data.get("target_ip", ""),
            current_state=obs_data.get("current_state", ""),
            output=obs_data.get("output", ""),
            difficulty=obs_data.get("difficulty", ""),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
