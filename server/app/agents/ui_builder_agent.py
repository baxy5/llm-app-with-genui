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
    Goal: Assemble already generated component descriptors (section, card(s), table(s)) into ONE final JSON UI event descriptor.

    IMPORTANT:
    - You DO NOT create new analytic components beyond those already available in state.
    - You ONLY reorganize/place existing descriptors into a nested structure.
    - If a section descriptor exists, it becomes the root component and all cards/tables are nested inside section.props.children (unless they are themselves nested sections already).
    - If NO section descriptor exists: create a synthetic root section to hold the cards/tables, with id derived from dashboard plan (fallback: assembled_dashboard_section).
    - You may create nested sections ONLY if an existing section descriptor implies subgrouping requirements in its naming or the dashboard_plan text clearly segments domains (e.g., "Customer Insights" separate from "Marketing Analytics"). Otherwise keep flat.

    OUTPUT (STRICT JSON ONLY):
    {
      "type": "ui_event",
      "target": "<target_id_from_state>",
      "component": {
         ... single root component (usually a section) embedding children ...
      }
    }

    Root component schema (section expected):
      id: string
      type: "section"
      props: {
        title: string (empty if missing)
        subtitle: string (empty if missing)
        loading: false
        children: [ componentObject, ... ]
      }

    Child component schemas must mirror their original agent outputs:
    Card child:
    {"id": "...", "type": "card", "props": {"title": "...", "value": "...", "description": "...", "trend": "up|down|flat|", "loading": bool}}

    Table child:
    {"id": "...", "type": "table", "props": {"title": "...", "loading": bool, "columns": [{"key": "...", "label": "..."}, ...], "rows": [ {<colKey>: value, ...}, ... ]}}

    Nested section child (only if already provided or clearly required by plan segmentation):
    {"id": "...", "type": "section", "props": {"title": "...", "subtitle": "...", "loading": false, "children": [ ... ]}}

    Assembly Rules:
    1. Preserve existing component ids and props EXACTLY; do not rename or alter metric values.
    2. If multiple cards/tables exist and no section descriptor: synthesize root section id from dashboard_plan main theme words (e.g., "Marketing Analytics" -> marketing_analytics_section). Subtitle may derive from remaining narrative.
    3. Do NOT duplicate components.
    4. Ensure every child has required props structure.
    5. loading should remain what original components specified (default false if absent).
    6. target MUST equal the provided target id from state.
    7. type MUST be "ui_event".

    Validation constraints:
    - Top-level keys ONLY: type, target, component.
    - component must be a single object (not an array) representing the root.
    - If no components exist at all (edge case), produce an empty root section with children: [] and reasonable id (empty_dashboard_section).
    - Do NOT add commentary or markdown.

    Return STRICT JSON.
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
