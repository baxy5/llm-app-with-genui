from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class SupervisorAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=env_config.OPENAI_API_KEY)

  async def supervise(self, state: MultiAgentState):
    messages = state["messages"]
    last_message = messages[-1]

    if not last_message:
      return {"current_agent": "supervisor"}

    supervisor_prompt = f"""
    You are a supervisor agent managing a multi-agent system. 
    Analyze the following user request and determine the best workflow:
    
    User request: {last_message.content if hasattr(last_message, "content") else str(last_message)}
    
    Available agents:
    1. researcher - For web searches and information gathering
    2. summary - For creating final responses and content
    3. chat - Handles direct questions, requirements or just chatting that don't require other agents' collaboration
    4. line_chart - For generating eChart options for a line chart.
    
    Current state:
    - Research data available: {bool(state.get("research_data"))}
    - Iteration: {state.get("iteration_count", 0)}
    
    Rules:
    - If research data is NOT available and the request requires external info → send to researcher.
    - If research data IS available → do NOT send to researcher again; instead, continue workflow (summary or line_chart depending on the request).
    - If the request is simple (no research or charts) → send to chat.
    - When all tasks are complete → respond with END.
    
    Respond with ONLY the next agent name that should handle this task: researcher, summary, chat, line_chart or END.
    """

    system_message = SystemMessage(content=supervisor_prompt)
    response = await self.llm.ainvoke([system_message])

    next_agent = response.content.strip().lower()

    print(f"SUPERVISOR: {next_agent}")
    print(f"ITERATION: {state.get('iteration_count', 0)}")

    if state.get("iteration_count", 0) > 5:
      next_agent = "END"

    return {
      "current_agent": next_agent,
      "iteration_count": state.get("iteration_count", 0) + 1,
    }
