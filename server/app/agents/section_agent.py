import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class SectionAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.llm = ChatOpenAI(model="gpt-4.1", api_key=env_config.OPENAI_API_KEY)
    self.llm_with_structured_output = self.llm.with_structured_output(method="json_mode")

  async def generate(self, state: MultiAgentState):
    dashboard_plan_state = state.get("dashboard_plan", {})

    if isinstance(dashboard_plan_state, dict):
      plan_text = dashboard_plan_state.get("dashboard_plan", "")
      todo = dashboard_plan_state.get("todo", {})
    else:
      plan_text = str(dashboard_plan_state)
      todo = {}

    section_prompt = """
    You are the Section Agent.
    Task: From the provided dashboard plan (text) and TODO list, produce ONLY the section container JSON.

    Scope limitations:
    - You MUST NOT generate card, table, chart, or other non-section component objects even if mentioned in later TODO steps.
    - Only create the section itself. Leave props.children empty OR include lightweight placeholders (id + type only) ONLY for components that are ALREADY explicitly stated as completed before section creation (usually none at this stage). If unsure, leave children as an empty list.
    - Do NOT fabricate data values (numbers, metrics) if not provided. Use empty strings or omit optional fields.

    Input structure explanation:
    - plan_text: free-form design narrative.
    - todo: an object with stepN entries. Identify the step that creates the section (look for keywords: "Create section" or type markers like section_...). Extract title/subtitle (or similar) from that step description.

    Output JSON schema (STRICT):
    {
      "id": "<section_id_snake_case>",
      "type": "section",
      "props": {
        "title": "<section title or empty if missing>",
        "subtitle": "<subtitle or empty if missing>",
        "loading": false,
        "children": []
      }
    }

    Rules for id derivation:
    - Lowercase.
    - Replace spaces with underscores.
    - Append "_section" if not already present.
    - If no title is available, use "untitled_section".

    Children rules:
    - Leave as [] unless prior steps (earlier than section step) clearly indicate a component already exists (rare). Do NOT include full props for other components.
    - If placeholders are included (only when clearly existing), each child minimal form: {"id": "<component_id>", "type": "<component_type>"}. No additional props.

    Validation constraints:
    - Must include id, type, props.title, props.subtitle, props.loading, props.children.
    - type MUST be "section".
    - props.children MUST be an array.
    - No extraneous top-level keys besides the specified schema.

    If required info (title/subtitle) missing, still return the schema with empty strings. Do NOT hallucinate.

    Return ONLY valid JSON conforming to the schema.

    Example (with placeholders omitted):
    {
      "id": "financial_overview_section",
      "type": "section",
      "props": {
        "title": "Financial Overview",
        "subtitle": "Key 2024 revenue metrics",
        "loading": False,
        "children": []
      }
    }
    """

    system_message = SystemMessage(content=section_prompt)
    human_message = HumanMessage(
      content=f"""
    plan_text: {plan_text}
    todo: {json.dumps(todo)}
    
    Provided data(s):
    1. Researched data: {state["research_data"]}
    
    2. Attachment data: {state["attachment_contents"]}
    """
    )

    message = [system_message, human_message]

    try:
      response = await self.llm_with_structured_output.ainvoke(message)

      dict_response = response if isinstance(response, dict) else json.loads(response)

      if dict_response and dict_response.get("id"):
        ui_event = {"type": "ui_event", "target": "loading_section", "component": dict_response}

        section_message = AIMessage(content=json.dumps(ui_event))
        messages = state.get("messages", [])
        messages.append(section_message)

        return {
          "section_component": dict_response,
          "current_agent": "component_supervisor",
          "messages": messages,
          "section_ready": True,
        }

      return {"section_component": dict_response, "current_agent": "component_supervisor"}
    except Exception as e:
      print(f"An error occurred while generating section component: {e}")
      return {"current_agent": "component_supervisor"}
