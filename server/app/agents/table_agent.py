import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class TableAgent:
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

    table_prompt = """
    You are the Table Agent.
    Task: From plan_text and TODO list, generate a single table component JSON descriptor for the next unfulfilled table-related step.

    Scope limitations:
    - Generate ONLY one table corresponding to the next unfulfilled TODO step that references a table.
    - Do NOT generate cards, sections, charts, or builder artifacts.
    - If no unfulfilled table step exists, return an empty JSON object {} (do NOT invent tables).

    Data usage:
    - Only use fields explicitly mentioned in the step description or known context.
    - Do NOT fabricate rows or data if unavailable.
    - If data is missing, output rows: [] and set loading=false (or loading=true if the description explicitly requires data acquisition).

    JSON schema (STRICT):
    {
      "id": "<snake_case_table_id>",
      "type": "table",
      "props": {
        "title": "<Title or empty>",
        "loading": false,
        "columns": [ {"key": "<field_key>", "label": "<Human Label>"}, ... ],
        "rows": [ {"<field_key>": <value or empty>}, ... ]
      }
    }

    ID derivation rules:
    - Lowercase alphanumeric with underscores, suffix _table.
    - Use main subject words from the step description (e.g., "Campaign Details" -> "campaign_details_table").
    - If duplicate candidate arises, append _2, _3, etc.

    Columns derivation:
    - Map columns to fields explicitly mentioned in description or known dataset fields.
    - If unknown fields → output [] (do not guess).

    Rows:
    - Each row object must use keys matching columns.key.
    - If no actual data → output [].
    - Numeric values should be numbers (percentages as numbers, not strings).

    Output format:
    - Single table → return JSON object matching schema above.
    - No unfulfilled table steps → return {}
    - NO markdown, NO commentary, STRICT JSON only.

    Validation constraints:
    - Object must include id, type="table", props.
    - props must include title, loading, columns, rows.
    - columns: array of objects with key & label.
    - rows: array of objects whose keys are subset of column keys.
    - loading must be boolean.

    Example (fulfilled step):
    {
      "id": "campaign_details_table",
      "type": "table",
      "props": {
        "title": "Campaign Details",
        "loading": false,
        "columns": [
          {"key": "campaign", "label": "Campaign Name"},
          {"key": "impressions", "label": "Impressions"},
          {"key": "clicks", "label": "Clicks"},
          {"key": "ctr", "label": "CTR %"},
          {"key": "cost", "label": "Cost ($)"}
        ],
        "rows": [
          {"campaign": "Summer Sale 2025", "impressions": 125000, "clicks": 4200, "ctr": 3.36, "cost": 2100}
        ]
      }
    }

    Example (no unfulfilled table step):
    {}
    """

    system_message = SystemMessage(content=table_prompt)
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

      dict_response = response if isinstance(response, (dict, list)) else json.loads(response)

      if dict_response and dict_response.get("id"):
        ui_event = {"type": "ui_event", "target": "loading_table", "component": dict_response}

        table_message = AIMessage(content=json.dumps(ui_event))
        messages = state.get("messages", [])
        messages.append(table_message)

        table_state = state.get("table_component", [])
        table_state.append(dict_response)

        return {
          "table_component": table_state,
          "current_agent": "component_supervisor",
          "messages": messages,
          "table_ready": True,
        }

      # Handle empty response
      table_state = state.get("table_component", [])
      table_state.append(dict_response)
      return {"table_component": table_state, "current_agent": "component_supervisor"}
    except Exception as e:
      print(f"An error occurred while generating table component: {e}")
      return {"current_agent": "component_supervisor"}
