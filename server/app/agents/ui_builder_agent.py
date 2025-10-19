import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class UiBuilderAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.llm = ChatOpenAI(model="gpt-4.1", api_key=env_config.OPENAI_API_KEY)
    self.llm_with_structured_output = self.llm.with_structured_output(method="json_mode")

  async def generate(self, state: MultiAgentState):
    dashboard_plan_state = state.get("dashboard_plan", {})
    ui_descriptor_target = state.get("ui_descriptor_target", "assembled_dashboard_section")

    if isinstance(dashboard_plan_state, dict):
      plan_text = dashboard_plan_state.get("dashboard_plan", "")
      todo = dashboard_plan_state.get("todo", {})
    else:
      plan_text = str(dashboard_plan_state)
      todo = {}

    ui_prompt = """
    You are the UI Builder Agent.

    Goal:
    - Assemble the already generated component descriptors (section, card(s), table(s)) into ONE final JSON UI event descriptor.

    Rules of engagement:
    - You DO NOT create new analytic components (cards, tables, charts, etc.).
    - You ONLY reorganize and nest existing descriptors into a valid UI event structure.

    Section usage logic (IMPORTANT):
    1. If an existing **section component descriptor** is available → use it as the root component.
      - Place all card(s)/table(s) under section.props.children (unless they already belong to nested sections).
    2. If NO section descriptor exists:
      - If there is **only one component** (a single card or a single table), return it **directly** as the `component` (no section wrapper).
      - If there are **multiple components**, synthesize a root section (id derived from dashboard plan, fallback: `assembled_dashboard_section`) to hold them in `children`.
    3. NEVER create a synthetic section for a single component.
    4. Nested sections may only be created if explicitly indicated by:
      - An existing section descriptor implying subgrouping, OR
      - The dashboard_plan text clearly segmenting domains (e.g., “Customer Insights” vs “Marketing Analytics”).
      Otherwise keep the structure flat.

    Output format (STRICT JSON ONLY):
    {
      "type": "ui_event",
      "target": "<target_id_from_state>",
      "component": {
        ... single root component (section OR single card/table) ...
      }
    }

    Component schemas:

    Section:
    {
      "id": "string",
      "type": "section",
      "props": {
        "title": "string (empty if missing)",
        "subtitle": "string (empty if missing)",
        "loading": false,
        "children": [ componentObject, ... ]
      }
    }

    Card:
    {
      "id": "string",
      "type": "card",
      "props": {
        "title": "string",
        "value": "string",
        "description": "string",
        "trend": "up|down|flat|",
        "loading": bool
      }
    }

    Table:
    {
      "id": "string",
      "type": "table",
      "props": {
        "title": "string",
        "loading": bool,
        "columns": [{"key": "string", "label": "string"}, ...],
        "rows": [ {<colKey>: value, ...}, ... ]
      }
    }

    Assembly Rules:
    1. Preserve all existing component IDs and props EXACTLY — do not rename, remove, or modify any metric or text value.
    2. Maintain the `loading` state as originally defined (default false if absent).
    3. If multiple cards/tables exist and no section descriptor:
      - Create a synthetic root section.
      - ID: derived from main theme words in dashboard_plan (fallback: assembled_dashboard_section).
      - Subtitle: optional, derived from plan text if helpful.
    4. NEVER duplicate or invent components.
    5. The top-level structure must always have:
      - "type": "ui_event"
      - "target": <target id from state>
      - "component": the final single root component (section or individual component)
    6. If no components exist at all, return an empty section:
      {
        "type": "ui_event",
        "target": "<target_id_from_state>",
        "component": {
          "id": "empty_dashboard_section",
          "type": "section",
          "props": {"title": "", "subtitle": "", "loading": false, "children": []}
        }
      }

    Validation constraints:
    - Top-level keys ONLY: type, target, component.
    - component must be ONE single object (not an array).
    - Return STRICT JSON (no markdown, no commentary).

    Example 1 — Section available:
    {
      "type": "ui_event",
      "target": "dashboard_root",
      "component": {
        "id": "marketing_section",
        "type": "section",
        "props": {
          "title": "Marketing Analytics",
          "subtitle": "",
          "loading": false,
          "children": [
            { "id": "total_revenue_card", "type": "card", "props": { ... } },
            { "id": "sales_table", "type": "table", "props": { ... } }
          ]
        }
      }
    }

    Example 2 — No section, one card only:
    {
      "type": "ui_event",
      "target": "dashboard_root",
      "component": {
        "id": "total_revenue_card",
        "type": "card",
        "props": { ... }
      }
    }

    Example 3 — No section, multiple components:
    {
      "type": "ui_event",
      "target": "dashboard_root",
      "component": {
        "id": "assembled_dashboard_section",
        "type": "section",
        "props": {
          "title": "Dashboard Overview",
          "subtitle": "",
          "loading": false,
          "children": [
            { "id": "open_tickets_card", "type": "card", "props": { ... } },
            { "id": "ticket_status_table", "type": "table", "props": { ... } }
          ]
        }
      }
    }
    """

    system_message = SystemMessage(content=ui_prompt)
    human_message = HumanMessage(
      content=f"""
    plan_text: {plan_text}
    todo: {json.dumps(todo)}
    target: {ui_descriptor_target}
    
    Available UI components:
    1. Section  component: {state["section_component"]}
    2. Table  component: {state["table_component"]}
    3. Card  component: {state["card_component"]}
    (Use these to generate the final UI descriptor.)
    """
    )

    message = [system_message, human_message]

    try:
      response = await self.llm_with_structured_output.ainvoke(message)

      dict_response = response if isinstance(response, dict) else json.loads(response)

      ui_message = AIMessage(content=json.dumps(dict_response))

      return {"ui_descriptor": dict_response, "messages": [ui_message], "current_agent": "END"}
    except Exception as e:
      print(f"An error occurred while generating UI descriptor: {e}")
      return {"current_agent": "component_supervisor"}
