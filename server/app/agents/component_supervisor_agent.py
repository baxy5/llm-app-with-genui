import json
import uuid

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class ComponentSupervisorAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.llm = ChatOpenAI(model="gpt-4.1", api_key=env_config.OPENAI_API_KEY)
    self.llm_with_structured_output = self.llm.with_structured_output(method="json_mode")

  async def supervise(self, state: MultiAgentState):
    last_message = state["messages"][-1].content
    existing_plan_data = state.get("dashboard_plan")  # may be dict or empty string
    has_existing_plan = isinstance(existing_plan_data, dict) and existing_plan_data.get(
      "dashboard_plan"
    )
    is_initial_planning = not has_existing_plan

    supervisor_prompt = """
    You are the Component Supervisor Agent.

    Goal:
      MODE A (initial planning - no prior plan): 
        - Produce (1) a concise interpretation of the user request,
          (2) a structured dashboard_plan of components,
          (3) a TODO list with fulfillment tracking,
          (4) determine the single next_agent to route to.
      MODE B (incremental update - prior plan exists): 
        - DO NOT alter the existing dashboard_plan.
        - Only update TODO fulfillment states or append new TODOs if new components are requested.
        - Return the SAME dashboard_plan verbatim.

    Available next agents (choose exactly one):
      card, table, section, ui_builder

    Decision heuristics:
      - section → container for multiple components.
      - card → singular KPI or metric.
      - table → multi-row data breakdown.
      - ui_builder → assemble when all components are complete.

    Data reasoning:
      - Map component ids to available data (research_data, attachment_contents).
      - Add clarifications if required data is missing.
      - Never invent data sources.

    DATA USAGE RULES:
      - Link matching field names in data (e.g. 'revenue', 'sales') to component ids.
      - Note explicitly: e.g. "using research_data['revenue']".
      - Do not invent new or undefined fields.

    COMPONENT FULFILLMENT CHECK (Critical):
      1. Extract each component id (card_*, table_*, section_*).
      2. Compare (case-insensitive) with existing component descriptors in the system state.
      3. Mark TODO as fulfilled=true if:
          - The component's id EXACTLY matches one from the provided state, OR
          - The component's type and key fields are already available.
      4. Fulfillment is sticky:
          - Once a TODO step is marked fulfilled, it stays fulfilled unless explicitly removed.
      5. When all TODO steps of a component type are fulfilled, skip routing back to that agent type.

    ROUTING SAFETY LOGIC:
      - After fulfillment check:
          * Gather all component types that have at least one unfulfilled TODO.
          * If none remain → next_agent="ui_builder".
          * If multiple types remain, pick the earliest unfulfilled step in TODO order.
      - Never pick the same agent type twice in a row unless:
          * A new TODO step for that type was added, AND
          * At least one unfulfilled step of that type still exists.
      - If all TODO steps for a type are fulfilled → permanently skip that agent type.

    MODE B strict rule:
      - dashboard_plan must be copied EXACTLY as received — no rewording or regeneration.

    Output format (strict JSON, no comments, no trailing commas):
    {
      "dashboard_plan": "<string>",
      "todo": {
        "step1": {"description": "1. ...", "fulfilled": false},
        "step2": {"description": "2. ...", "fulfilled": true}
      },
      "next_agent": "card",
      "mode_used": "A"
    }

    Validation rules:
      - Only one of [card, table, section, ui_builder] is allowed as next_agent.
      - dashboard_plan must reference every component mentioned in TODOs.
      - Never output markdown or explanations.

    Example:
    {
      "dashboard_plan": "Create 'Financial Overview' section with cards for Total Revenue and Avg Monthly Revenue, and a table for Revenue by Quarter.",
      "todo": {
        "step1": {"description": "1. Create section 'Financial Overview'", "fulfilled": false},
        "step2": {"description": "2. Create card card_total_revenue_2024 using sum(revenue) from research_data['revenue']", "fulfilled": true},
        "step3": {"description": "3. Create card card_avg_monthly_revenue using avg(revenue) from research_data['revenue']", "fulfilled": true},
        "step4": {"description": "4. Create table table_revenue_by_quarter using research_data['revenue']", "fulfilled": false},
        "step5": {"description": "5. Assemble all components using UI Builder", "fulfilled": false}
      },
      "next_agent": "table",
      "mode_used": "B"
    }
    """

    system_message = SystemMessage(content=supervisor_prompt)
    human_message = HumanMessage(
      content=f"""
    User request: {last_message}
    
    Provided data(s):
    1. Researched data: {state["research_data"]}
    
    2. Attachment data: {state["attachment_contents"]}
    
    Existing dashboard_plan (if any): {existing_plan_data}

    Available component descriptors:
    1. Section component(s): {state.get("section_component", {})}
    2. Card component(s): {state.get("card_component", [])}
    3. Table component(s): {state.get("table_component", [])}
    (Use these to mark fulfilled steps before choosing next_agent.)
    """
    )

    message = [system_message] + [human_message]

    try:
      response = await self.llm_with_structured_output.ainvoke(message)

      dict_response = response if isinstance(response, dict) else json.loads(response)

      plan = dict_response["dashboard_plan"]
      # Preserve original plan if existing (MODE B) regardless of model output alterations
      if has_existing_plan and isinstance(existing_plan_data, dict):
        original_plan_text = existing_plan_data.get("dashboard_plan", "")
        if original_plan_text:
          plan = original_plan_text
      todo = dict_response["todo"]

      dashboard_plan = {"dashboard_plan": plan, "todo": todo}
      next_agent = dict_response["next_agent"]

      print("\n\n" + "-" * 40)
      print("COMPONENT SUPERVISOR NEXT AGENT:")
      print(next_agent)
      print("-" * 40)

      if state.get("iteration_count", 0) > 5:
        next_agent = "END"

      if is_initial_planning:
        ui_descriptor_target = f"component-{str(uuid.uuid4().int)[:5]}"
      else:
        ui_descriptor_target = state.get("ui_descriptor_target", "")

      return {
        "dashboard_plan": dashboard_plan,
        "current_agent": next_agent,
        "is_initial_planning": is_initial_planning,
        "ui_descriptor_target": ui_descriptor_target,
      }
    except Exception as e:
      print(f"An error occurred while generating dashboard plan in Component Supervisor Agent: {e}")
      return {"current_agent": "END"}
