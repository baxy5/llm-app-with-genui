import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class CardAgent:
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

    card_prompt = """
    You are the Card Agent.

    Task:
    - Using the dashboard plan narrative (plan_text) and TODO list, generate a single card component JSON descriptor for the next unfulfilled card-related step.

    Scope limitations:
    - Generate ONLY one card corresponding to the next unfulfilled TODO step that references a card.
    - Do NOT generate tables, sections, charts, or UI builder artifacts.
    - If no unfulfilled card step exists, return an empty JSON object {} (do NOT invent cards).

    Data usage:
    - Each TODO step may mention data fields, aggregations, filters, or metrics.
    - Use only information explicitly available in the step description or known context.
    - If a numeric value is missing, set "value": "" and "loading": false (or "loading": true if the description clearly indicates missing data).
    - Do NOT fabricate precise numbers.
    - "trend" can be one of ["up", "down", "neutral", ""] (empty string if unknown).

    JSON schema (STRICT):
    {
      "id": "<snake_case_card_id>",
      "type": "card",
      "props": {
        "title": "<Title or empty>",
        "value": "<Value or empty>",
        "description": "<Short description or empty>",
        "trend": "up|down|neutral|",
        "loading": false,
        "unit": "<unit or empty>",
        "previousValue": <number or null>,
        "delta": <number or null>,
        "trendColor": "<color or empty>",
        "size": "sm|md|lg",
        "bordered": true|false,
        "shadow": true|false,
        "rounded": true|false,
        "className": "<string or empty>",
        "progress": <number 0-100 or null>,
        "progressColor": "<color or empty>",
        "children": [] 
      }
    }

    ID derivation rules:
    - Lowercase alphanumeric with underscores only.
    - Base id on key metric words from the step (e.g., "Total Revenue" → "total_revenue_card").
    - Ensure suffix "_card".
    - If the same id already exists in context, append a numeric suffix (_2, _3, etc.).

    Output rules:
    - If an unfulfilled card step exists → return a SINGLE JSON object matching the schema above.
    - If no unfulfilled card step exists → return {}.
    - NO markdown, NO commentary, STRICT JSON only.

    Validation constraints:
    - Object must include: id, type="card", props.
    - props must include all extended card props listed in the schema above.
    - No extra top-level keys.
    - loading must be boolean.

    Example (fulfilled case):
    {
      "id": "total_revenue_card",
      "type": "card",
      "props": {
        "title": "Total Revenue",
        "value": "120K",
        "description": "Sum of all sales this quarter",
        "trend": "up",
        "loading": false,
        "unit": "$",
        "previousValue": 100000,
        "delta": 20000,
        "trendColor": "text-green-500",
        "size": "md",
        "bordered": true,
        "shadow": true,
        "rounded": true,
        "className": "",
        "progress": 50,
        "progressColor": "bg-blue-500",
        "children": []
      }
    }

    Example (no unfulfilled card step):
    {}
    """

    system_message = SystemMessage(content=card_prompt)
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

      card_state = state.get("card_component", [])
      card_state.append(dict_response)

      return {"card_component": card_state, "current_agent": "component_supervisor"}
    except Exception as e:
      print(f"An error occurred while generating card component: {e}")
      return {"current_agent": "component_supervisor"}
