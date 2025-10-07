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
    2. summary - For creating final responses and content analysis
    3. chat - Handles direct questions, requirements or just chatting that don't require other agents' collaboration
    4. line_chart - For generating eChart options for a line chart
    5. bar_chart - For generating eChart options for a bar chart
    
    Current state:
    - Research data {"IS available" if state.get("research_data") else "is NOT available"}
    - User attached file data {"IS available" if state.get("attachment_contents") else "is NOT available"}
    - Iteration: {state.get("iteration_count", 0)}
    
    ENHANCED ANALYSIS RULES:
    1. PARSE USER REQUEST FOR SPECIFIC FILE REFERENCES:
       - Look for keywords like "Excel file", "PDF document", "first file", "second attachment", etc.
       - Identify if user wants to work with ALL files or SPECIFIC files
       - Note file format preferences (Excel, PDF, CSV, etc.)
    
    2. ROUTING LOGIC:
       - If research data is NOT available and request requires external information → researcher
       - If research data IS available → do NOT send to researcher again
       - If user attached file data IS available:
         * For analysis/summary requests (keywords: analyze, summarize, extract, insights, explain, interpret) → summary
         * For visualization requests (keywords: chart, plot, graph, visualize, trend, dashboard) →
           - Line chart keywords: line chart, time series, trend over time, temporal data → line_chart
           - Bar chart keywords: bar chart, comparison, categories, ranking, distribution → bar_chart
         * For file-specific questions with clear file references → summary
       - If no file data and simple question → chat
       - If complex question without files → researcher then summary
    
    3. SPECIAL HANDLING:
       - If user mentions specific file types or positions ("the Excel file", "PDF only") → pass this context to chosen agent
       - If request is ambiguous about which files to use → default to summary for clarification
       - When all processing complete → END
    
    Respond with ONLY the next agent name: researcher, summary, chat, line_chart, bar_chart, or END.
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
