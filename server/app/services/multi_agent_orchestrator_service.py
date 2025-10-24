import json
import logging
import os
from typing import Annotated

from fastapi import Depends, Request
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver, RunnableConfig
from langgraph.graph import END, StateGraph
from requests import Session

from app.agents.bar_chart_agent import BarChartAgent
from app.agents.card_agent import CardAgent
from app.agents.chat_agent import ChatAgent
from app.agents.component_supervisor_agent import ComponentSupervisorAgent
from app.agents.line_chart_agent import LineChartAgent
from app.agents.research_agent import ResearchAgent
from app.agents.section_agent import SectionAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.table_agent import TableAgent
from app.agents.ui_builder_agent import UiBuilderAgent
from app.db.database import get_db
from app.models.state_model import MultiAgentRequest, MultiAgentState
from app.services.chat_session_service import ChatSessionService
from app.services.env_config_service import EnvConfigService, get_env_configs
from app.services.file_service import FileService, get_file_service_db_session

logger = logging.getLogger(__name__)


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
  ):
    self.env_config = env_config
    self.checkpointer = checkpointer
    self.cs_service = cs_service
    self.file_service = file_service

    self.supervisor_agent = SupervisorAgent(env_config=env_config)
    self.research_agent = ResearchAgent(env_config=env_config)
    self.summary_agent = SummaryAgent(env_config=env_config)
    self.chat_agent = ChatAgent(env_config=env_config)
    self.line_chart_agent = LineChartAgent(env_config=env_config)
    self.bar_chart_agent = BarChartAgent(env_config=env_config)
    self.component_supervisor_agent = ComponentSupervisorAgent(env_config=env_config)
    self.section_agent = SectionAgent(env_config=env_config)
    self.card_agent = CardAgent(env_config=env_config)
    self.table_agent = TableAgent(env_config=env_config)
    self.ui_builder_agent = UiBuilderAgent(env_config=env_config)

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
    graph.add_node("component_supervisor_agent", self.component_supervisor_agent.supervise)
    graph.add_node("section_agent", self.section_agent.generate)
    graph.add_node("card_agent", self.card_agent.generate)
    graph.add_node("table_agent", self.table_agent.generate)
    graph.add_node("ui_builder_agent", self.ui_builder_agent.generate)

    available_agents = [
      "supervisor_agent",
      "research_agent",
      "summary_agent",
      "chat_agent",
      "line_chart_agent",
      "bar_chart_agent",
      "component_supervisor_agent",
      "section_agent",
      "card_agent",
      "table_agent",
      "ui_builder_agent",
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
        "component_supervisor",
        "section",
        "card",
        "table",
        "ui_builder",
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
          "component_supervisor": "component_supervisor_agent",
          "section": "section_agent",
          "card": "card_agent",
          "table": "table_agent",
          "ui_builder": "ui_builder_agent",
          END: END,
        },
      )

    return graph.compile(checkpointer=self.checkpointer)

  def serialise_ai_message_chunk(self, chunk):
    if isinstance(chunk, AIMessageChunk):
      return chunk.content
    else:
      logger.error(
        f"Object of type {type(chunk).__name__} is not correctly formatted for serialisation"
      )
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
      "iteration_count": 0,
      "attachment_contents": content,
      "dashboard_plan": {},
      "section_component": {},
      "card_component": [],
      "table_component": [],
      "is_initial_planning": True,
      "ui_descriptor": {},
      "ui_descriptor_target": None,
      "section_ready": False,
      "card_ready": False,
      "table_ready": False,
      "messages": [HumanMessage(content=req.input)],
    }

    events = self.graph.astream_events(initial_state, version="v2", config=config)

    # Component counters for unique IDs
    component_counters = {"section": 0, "card": 0, "table": 0}

    # Track components for database saving
    collected_components = []

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
          yield 'data: {"type": "progress", "content": "Summarizing findings", "icon": "pencil"}\n\n'
        elif event_name == "chat_agent":
          yield 'data: {"type": "progress", "content": "Generating response", "icon": "pencil"}\n\n'
        elif event_name == "supervisor_agent":
          yield 'data: {"type": "progress", "content": "Planning next step", "icon": "brain"}\n\n'
        elif event_name == "line_chart_agent":
          yield 'data: {"type": "progress", "content": "Generating line chart", "icon": "line_chart"}\n\n'
        elif event_name == "bar_chart_agent":
          yield 'data: {"type": "progress", "content": "Generating bar chart", "icon": "bar_chart"}\n\n'
        elif event_name == "section_agent":
          yield 'data: {"type": "progress", "content": "Building Section UI component", "icon": "blocks"}\n\n'
          component_counters["section"] += 1
          unique_target = f"section_component_{component_counters['section']}"
          ui_data = {
            "type": "ui_event",
            "target": unique_target,
            "component": {
              "id": unique_target,
              "type": "section",
              "props": {
                "title": "",
                "subtitle": "",
                "loading": True,
                "children": [],
              },
            },
          }
          payload = {"type": "content", "component": [ui_data]}
          yield f"data: {json.dumps(payload)}\n\n"
        elif event_name == "table_agent":
          yield 'data: {"type": "progress", "content": "Building Table UI component", "icon": "blocks"}\n\n'
          # Send skeleton loader for table with unique ID
          component_counters["table"] += 1
          unique_target = f"table_component_{component_counters['table']}"
          ui_data = {
            "type": "ui_event",
            "target": unique_target,
            "component": {
              "id": unique_target,
              "type": "table",
              "props": {
                "title": "",
                "loading": True,
                "columns": [],
                "rows": [],
              },
            },
          }
          payload = {"type": "content", "component": [ui_data]}
          yield f"data: {json.dumps(payload)}\n\n"
        elif event_name == "card_agent":
          yield 'data: {"type": "progress", "content": "Building Card UI component", "icon": "blocks"}\n\n'
          # Send skeleton loader for card with unique ID
          component_counters["card"] += 1
          unique_target = f"card_component_{component_counters['card']}"
          ui_data = {
            "type": "ui_event",
            "target": unique_target,
            "component": {
              "id": unique_target,
              "type": "card",
              "props": {
                "title": "",
                "value": "",
                "loading": True,
                "size": "md",
                "bordered": True,
                "shadow": True,
                "rounded": True,
                "children": [],
              },
            },
          }
          payload = {"type": "content", "component": [ui_data]}
          yield f"data: {json.dumps(payload)}\n\n"

      # Handle agent completion events
      if event_type == "on_chain_end":
        if event_name == "research_agent":
          yield 'data: {"type": "progress", "content": "Research completed", "icon": "check"}\n\n'
        elif event_name == "summary_agent":
          yield 'data: {"type": "progress", "content": "Summary completed", "icon": "check"}\n\n'
        elif event_name == "chat_agent":
          yield 'data: {"type": "progress", "content": "Response completed", "icon": "check"}\n\n'
        elif event_name == "component_supervisor_agent":
          pass
        elif event_name == "section_agent":
          event_data = event.get("data", {})
          output = event_data.get("output", {})

          if output.get("section_ready") and output.get("messages"):
            section_ui_event = json.loads(output["messages"][-1].content)
            target_id = f"section_component_{component_counters['section']}"
            section_ui_event["target"] = target_id
            payload = {"type": "content", "component": [section_ui_event]}
            yield f"data: {json.dumps(payload)}\n\n"

            # Collect component for database saving
            collected_components.append(section_ui_event)

          yield 'data: {"type": "progress", "content": "Section UI component crafted", "icon": "check"}\n\n'
        elif event_name == "table_agent":
          event_data = event.get("data", {})
          output = event_data.get("output", {})

          # Handle progressive component delivery - replace skeleton loader
          if output.get("table_ready") and output.get("messages"):
            # Send the actual table descriptor with target matching current table counter
            table_ui_event = json.loads(output["messages"][-1].content)
            # Use the current table counter to determine target
            target_id = f"table_component_{component_counters['table']}"
            table_ui_event["target"] = target_id
            payload = {"type": "content", "component": [table_ui_event]}
            yield f"data: {json.dumps(payload)}\n\n"

            # Collect component for database saving
            collected_components.append(table_ui_event)

          yield 'data: {"type": "progress", "content": "Table UI component crafted", "icon": "check"}\n\n'
        elif event_name == "card_agent":
          event_data = event.get("data", {})
          output = event_data.get("output", {})

          # Handle progressive component delivery - replace skeleton loader
          if output.get("card_ready") and output.get("messages"):
            # Send the actual card descriptor with target matching current card counter
            card_ui_event = json.loads(output["messages"][-1].content)
            # Use the current card counter to determine target
            target_id = f"card_component_{component_counters['card']}"
            card_ui_event["target"] = target_id
            payload = {"type": "content", "component": [card_ui_event]}
            yield f"data: {json.dumps(payload)}\n\n"

            # Collect component for database saving
            collected_components.append(card_ui_event)

          yield 'data: {"type": "progress", "content": "Card UI component crafted", "icon": "check"}\n\n'
        elif event_name == "ui_builder_agent":
          # UI builder is no longer needed since components are sent progressively
          # But we can still use it to mark completion of the component assembly process
          event_data = event.get("data", {})
          output = event_data.get("output", {})
          if output and "messages" in output and output["messages"] and not collected_components:
            # Fallback: if no progressive components were collected, use UI builder result
            ui_data = json.loads(output["messages"][0].content)
            collected_components.append(ui_data)
          yield 'data: {"type": "progress", "content": "Component(s) crafted, dashboard assembled", "icon": "check"}\n\n'
        # Line Chart final response
        elif event_name == "line_chart_agent":
          event_data = event.get("data", {})
          output = event_data.get("output", {})
          if output and "messages" in output and output["messages"]:
            chart_data = json.loads(output["messages"][0].content)
            final_response = chart_data
            payload = {"type": "content", "option": chart_data}
            yield f"data: {json.dumps(payload)}\n\n"
          yield 'data: {"type": "progress", "content": "Line chart generation completed", "icon": "check"}\n\n'
        # Bar Chart final response
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
        elif event_metadata_node == "component_supervisor_agent":
          continue
        elif event_metadata_node == "section_agent":
          continue
        elif event_metadata_node == "card_agent":
          continue
        elif event_metadata_node == "table_agent":
          continue
        elif event_metadata_node == "ui_builder_agent":
          continue
        else:
          chunk_content = self.serialise_ai_message_chunk(event["data"]["chunk"])
          final_response += chunk_content
          payload = {"type": "content", "content": chunk_content}
          yield f"data: {json.dumps(payload)}\n\n"

    # Store agent response to db
    if collected_components:
      # progressive components
      await self.cs_service.add_assistant_message(
        session_id=req.session_id, component=collected_components, content=None, option=None
      )
    elif isinstance(final_response, str) and final_response.strip():
      # text basde
      await self.cs_service.add_assistant_message(
        session_id=req.session_id, content=final_response, option=None, component=None
      )
    elif isinstance(final_response, list):
      # If we have a list response (shouldn't happen with new flow)
      await self.cs_service.add_assistant_message(
        session_id=req.session_id, component=final_response, content=None, option=None
      )
    elif final_response and not isinstance(final_response, str):
      # chart
      await self.cs_service.add_assistant_message(
        session_id=req.session_id, content=None, option=final_response, component=None
      )
    else:
      await self.cs_service.add_assistant_message(
        session_id=req.session_id, content="", option=None, component=None
      )

    yield 'data: {"type": "end"}\n\n'
