import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AnyMessage
from pydantic import BaseModel


class MultiAgentState(TypedDict):
  current_agent: str
  research_data: str
  iteration_count: int = 0
  messages: Annotated[Sequence[AnyMessage], operator.add]


class MultiAgentRequest(BaseModel):
  input: str
  session_id: str
