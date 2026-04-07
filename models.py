from pydantic import BaseModel, Field
from openenv.core.env_server import Action, Observation, State
from typing import Literal, List, Dict

class RedTeamAction(Action):
    action: Literal["scan", "enumerate", "exploit", "escalate", "c2", "cleanup"] = Field(
        ..., description="Red team action to execute"
    )

class RedTeamObservation(Observation):
    target_ip: str
    current_state: str
    output: str
    difficulty: str

class RedTeamState(State):
    episode: int
    task: str
    progress: float
