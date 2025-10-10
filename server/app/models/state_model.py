import operator
from typing import Annotated, List, Optional, Sequence, TypedDict

from langchain_core.messages import AnyMessage
from pydantic import BaseModel


class FileMetadata(BaseModel):
  file_id: int
  session_id: int
  filename: str
  file_hash: str
  content_type: str
  upload_time: Optional[str] = None
  content: Optional[str] = None


class MultiAgentState(TypedDict):
  current_agent: str
  research_data: str
  database_query: str
  database_data: List[dict]
  iteration_count: int = 0
  attachment_contents: str = None
  messages: Annotated[Sequence[AnyMessage], operator.add]


class MultiAgentRequest(BaseModel):
  input: str
  session_id: str
