import json
import os
from typing import Annotated

from fastapi import Depends, Request
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver, RunnableConfig
from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agents.bar_chart_agent import BarChartAgent
from app.agents.chat_agent import ChatAgent
from app.agents.line_chart_agent import LineChartAgent
from app.agents.research_agent import ResearchAgent
from app.agents.sql_query_agent import SqlQueryAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.db.database import get_db
from app.models.state_model import MultiAgentRequest, MultiAgentState
from app.services.chat_session_service import ChatSessionService
from app.services.dataset_service import DatasetService
from app.services.env_config_service import EnvConfigService, get_env_configs
from app.services.file_service import FileService, get_file_service_db_session


def get_checkpointer(req: Request) -> BaseCheckpointSaver:
  return req.app.state.checkpointer


def get_db_session(
  db: Session = Depends(get_db), checkpointer: BaseCheckpointSaver = Depends(get_checkpointer)
) -> ChatSessionService:
  return ChatSessionService(db, checkpointer)


class MultiAgentOrchestratorService:
  """Main orchestrator that manages the multi-agent workflow using Langgraph."""

  def __init__(
    self,
    env_config: Annotated[EnvConfigService, Depends(get_env_configs)],
    checkpointer: Annotated[BaseCheckpointSaver, Depends(get_checkpointer)],
    cs_service: Annotated[ChatSessionService, Depends(get_db_session)],
    file_service: Annotated[FileService, Depends(get_file_service_db_session)],
    db: Session = Depends(get_db),
  ):
    self.env_config = env_config
    self.checkpointer = checkpointer
    self.cs_service = cs_service
    self.file_service = file_service

    dataset_service = DatasetService(db)

    self.supervisor_agent = SupervisorAgent(env_config=env_config, dataset_service=dataset_service)
    self.research_agent = ResearchAgent(env_config=env_config)
    self.summary_agent = SummaryAgent(env_config=env_config)
    self.chat_agent = ChatAgent(env_config=env_config)
    self.line_chart_agent = LineChartAgent(env_config=env_config)
    self.bar_chart_agent = BarChartAgent(env_config=env_config)
    self.query_agent = SqlQueryAgent(env_config=env_config)

    self.graph = self._build_multi_agent_graph()

  def _build_multi_agent_graph(self):
    """Build the multi-agent workflow graph."""
    graph = StateGraph(MultiAgentState)

    graph.add_node("supervisor_agent", self.supervisor_agent.supervise)
    graph.add_node("research_agent", self.research_agent.research)
    graph.add_node("summary_agent", self.summary_agent.summary)
    graph.add_node("chat_agent", self.chat_agent.chat)
    graph.add_node("line_chart_agent", self.line_chart_agent.chart)
    graph.add_node("bar_chart_agent", self.bar_chart_agent.chart)
    graph.add_node("query_agent", self.query_agent.generate)

    available_agents = [
      "supervisor_agent",
      "research_agent",
      "summary_agent",
      "chat_agent",
      "line_chart_agent",
      "bar_chart_agent",
      "query_agent",
    ]

    def route_to_agent(state: MultiAgentState):
      current_agent = state.get("current_agent", "supervisor")

      if current_agent == "END":
        return END
      elif current_agent in [
        "supervisor",
        "researcher",
        "summary",
        "chat",
        "line_chart",
        "bar_chart",
        "query",
      ]:
        return current_agent
      else:
        return "supervisor"

    graph.set_entry_point("supervisor_agent")

    for agent in available_agents:
      graph.add_conditional_edges(
        agent,
        route_to_agent,
        {
          "supervisor": "supervisor_agent",
          "researcher": "research_agent",
          "summary": "summary_agent",
          "chat": "chat_agent",
          "line_chart": "line_chart_agent",
          "bar_chart": "bar_chart_agent",
          "query": "query_agent",
          END: END,
        },
      )

    return graph.compile(checkpointer=self.checkpointer)

  def serialise_ai_message_chunk(self, chunk):
    if isinstance(chunk, AIMessageChunk):
      return chunk.content
    else:
      raise TypeError(
        f"Object of type {type(chunk).__name__} is not correctly formatted for serialisation"
      )

  def draw_graph(self) -> None:
    os.makedirs("images", exist_ok=True)
    self.graph.get_graph().draw_mermaid_png(output_file_path="images/graph.png")

  async def generate(self, req: MultiAgentRequest):
    # self.draw_graph()

    config = RunnableConfig(configurable={"thread_id": req.session_id})

    # Return files' content if provided
    try:
      content = await self.file_service.retrieve_content_by_session_id(int(req.session_id))
    except Exception:
      content = None

    initial_state = {
      "research_data": "",
      "database_query": None,
      "database_data": None,
      "iteration_count": 0,
      "attachment_contents": content,
      "messages": [HumanMessage(content=req.input)],
    }

    events = self.graph.astream_events(initial_state, version="v2", config=config)

    final_response: str | dict = ""
    async for event in events:
      event_type = event["event"]
      event_name = event["name"]
      event_metadata_node = event.get("metadata", {}).get("langgraph_node")

      # Handle progress events when agents start
      if event_type == "on_chain_start":
        if event_name == "research_agent":
          yield 'data: {"type": "progress", "content": "Researching information", "icon": "text_search"}\n\n'
        elif event_name == "summary_agent":
          yield 'data: {"type": "progress", "content": "Summarizing findings", "icon": "notebook"}\n\n'
        elif event_name == "chat_agent":
          yield 'data: {"type": "progress", "content": "Generating response", "icon": "notebook"}\n\n'
        elif event_name == "supervisor_agent":
          yield 'data: {"type": "progress", "content": "Planning next step", "icon": "brain"}\n\n'
        elif event_name == "line_chart_agent":
          yield 'data: {"type": "progress", "content": "Generating line chart", "icon": "notebook"}\n\n'
        elif event_name == "bar_chart_agent":
          yield 'data: {"type": "progress", "content": "Generating bar chart", "icon": "notebook"}\n\n'

      # Handle agent completion events
      if event_type == "on_chain_end":
        if event_name == "research_agent":
          yield 'data: {"type": "progress", "content": "Research completed", "icon": "check"}\n\n'
        elif event_name == "summary_agent":
          yield 'data: {"type": "progress", "content": "Summary completed", "icon": "check"}\n\n'
        elif event_name == "chat_agent":
          yield 'data: {"type": "progress", "content": "Response completed", "icon": "check"}\n\n'
        elif event_name == "line_chart_agent":
          event_data = event.get("data", {})
          output = event_data.get("output", {})
          if output and "messages" in output and output["messages"]:
            chart_data = json.loads(output["messages"][0].content)
            final_response = chart_data
            payload = {"type": "content", "option": chart_data}
            yield f"data: {json.dumps(payload)}\n\n"
          yield 'data: {"type": "progress", "content": "Line chart generation completed", "icon": "check"}\n\n'
        elif event_name == "bar_chart_agent":
          event_data = event.get("data", {})
          output = event_data.get("output", {})
          if output and "messages" in output and output["messages"]:
            chart_data = json.loads(output["messages"][0].content)
            final_response = chart_data
            payload = {"type": "content", "option": chart_data}
            yield f"data: {json.dumps(payload)}\n\n"
          yield 'data: {"type": "progress", "content": "Bar chart generation completed", "icon": "check"}\n\n'

      if event_type == "on_tool_start":
        tool_name = event["name"]

        if tool_name == "tavily_search_tool":
          tool_input = event.get("data", {}).get("input", {})
          search_query = tool_input.get("input", "") if isinstance(tool_input, dict) else ""
          payload = {
            "type": "progress",
            "content": "Searching on the web",
            "search_query": search_query,
            "icon": "search",
          }
          yield f"data: {json.dumps(payload)}\n\n"

      if event_type == "on_tool_end":
        tool_name = event["name"]
        if tool_name == "tavily_search_tool":
          payload = {
            "type": "progress",
            "content": "Web search completed",
            "icon": "check",
          }
          yield f"data: {json.dumps(payload)}\n\n"

      # Handle streaming content
      if event_type == "on_chat_model_stream":
        if event_metadata_node == "supervisor_agent":
          continue
        elif event_metadata_node == "research_agent":
          continue
        elif event_metadata_node == "line_chart_agent":
          continue
        elif event_metadata_node == "bar_chart_agent":
          continue
        elif event_metadata_node == "query_agent":
          continue
        else:
          chunk_content = self.serialise_ai_message_chunk(event["data"]["chunk"])
          final_response += chunk_content
          payload = {"type": "content", "content": chunk_content}
          yield f"data: {json.dumps(payload)}\n\n"

    # Store agent response to db
    if isinstance(final_response, str):
      await self.cs_service.add_assistant_message(
        session_id=req.session_id, content=final_response, option=None
      )
    else:
      await self.cs_service.add_assistant_message(
        session_id=req.session_id, content=None, option=final_response
      )

    yield 'data: {"type": "end"}\n\n'
