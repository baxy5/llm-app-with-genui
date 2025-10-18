import operator
from typing import Annotated, Any, NotRequired, Sequence, TypedDict

from langchain_core.messages import AnyMessage
from pydantic import BaseModel


class MultiAgentState(TypedDict):
  current_agent: str
  research_data: str
  attachment_contents: NotRequired[str | None]
  dashboard_plan: dict[str, Any]
  section_component: dict
  card_component: list[dict]
  table_component: list[dict]
  ui_descriptor: dict
  ui_descriptor_target: str
  is_initial_planning: bool
  iteration_count: int
  messages: Annotated[Sequence[AnyMessage], operator.add]


class MultiAgentRequest(BaseModel):
  input: str
  session_id: str
