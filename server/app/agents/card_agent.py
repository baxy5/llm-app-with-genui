import json
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService

logger = logging.getLogger(__name__)


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

    Data handling principles:
    - Only include properties for which reliable data or intent is explicitly mentioned.
    - If a property's value is unknown or cannot be inferred, omit that property entirely.
    - Never fabricate values, units, descriptions, or trends.
    - When omitting a property, you must still return a valid JSON object following the schema, but unused or unavailable props may be excluded (e.g., exclude `delta` if no prior value is referenced).
    - Boolean and enum fields (e.g., `loading`, `bordered`, `shadow`, `rounded`) should still be included to maintain consistent component behavior.
    - Numeric fields without data (e.g., value, delta, progress) must NOT be guessed or approximated.
    - The "trend" field must only be one of ["up", "down", "neutral"] if clearly mentioned, otherwise omit it.

    JSON schema (flexible but valid):
    {
      "id": "<snake_case_card_id>",
      "type": "card",
      "props": {
        "title": "<Title or empty>",
        "value": "<Value if known>",
        "description": "<Short description if known>",
        "trend": "up|down|neutral" (optional),
        "loading": false,
        "unit": "<unit if specified>",
        "previousValue": <number or null> (optional),
        "delta": <number or null> (optional),
        "trendColor": "<color or empty>" (optional),
        "size": "sm|md|lg",
        "bordered": true,
        "shadow": true,
        "rounded": true,
        "className": "<string or empty>",
        "progress": <number 0-100> (optional),
        "progressColor": "<color or empty>" (optional),
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
    - Object must include: id, type="card", and props.
    - props must include all standard style/configuration fields (size, bordered, shadow, rounded, className, children).
    - Optional data fields (like delta, progress, trend, etc.) may be omitted entirely if not supported by context.

    Example (fulfilled case with available data):
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

    Example (partial data case):
    {
      "id": "open_tickets_card",
      "type": "card",
      "props": {
        "title": "Open Tickets",
        "loading": true,
        "size": "sm",
        "bordered": true,
        "shadow": true,
        "rounded": true,
        "className": "",
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
      logger.debug("Generating card response.")
      response = await self.llm_with_structured_output.ainvoke(message)

      dict_response = response if isinstance(response, dict) else json.loads(response)

      if dict_response and dict_response.get("id"):
        ui_event = {"type": "ui_event", "target": "loading_card", "component": dict_response}

        card_message = AIMessage(content=json.dumps(ui_event))
        messages = state.get("messages", [])
        messages.append(card_message)

        card_state = state.get("card_component", [])
        card_state.append(dict_response)

        return {
          "card_component": card_state,
          "current_agent": "component_supervisor",
          "messages": messages,
          "card_ready": True,
        }
      else:
        logger.error("Card model validation failed.")

      # Handle empty response
      card_state = state.get("card_component", [])
      card_state.append(dict_response)
      return {"card_component": card_state, "current_agent": "component_supervisor"}
    except Exception as e:
      logger.error(f"Failed to generate card component: {e}")
      return {"current_agent": "component_supervisor"}
