from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.dataset_service import DatasetService
from app.services.env_config_service import EnvConfigService


class SupervisorAgent:
  def __init__(
    self,
    env_config: EnvConfigService,
    dataset_service: DatasetService = None,
  ):
    self.env_config = env_config
    self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=env_config.OPENAI_API_KEY)
    self.dataset_service = dataset_service

  async def supervise(self, state: MultiAgentState):
    messages = state["messages"]
    last_message = messages[-1]

    database_query = state.get("database_query")
    if database_query and database_query != "False" and self.dataset_service:
      print(f"Database query: {database_query}")
      try:
        data = self.dataset_service.run_sql_query(database_query)
        state["database_data"] = data
        print(f"Database data: {state['database_data']}")
      except Exception as e:
        print(f"Error executing database query: {e}")
    else:
      state["database_data"] = None

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
    6. query - For generating SQL query from database "dataset" table
    
    Current state:
    - Research data {"IS available" if state.get("research_data") else "is NOT available"}
    - Database data {"IS available" if state.get("database_data") else "is NOT available"}
    - User attached file data {"IS available" if state.get("attachment_contents") else "is NOT available"}
    - Iteration: {state.get("iteration_count", 0)}
    
    ENHANCED ANALYSIS RULES:
    1. PARSE USER REQUEST FOR SPECIFIC FILE REFERENCES:
       - Look for keywords like "Excel file", "PDF document", "first file", "second attachment", etc.
       - Identify if user wants to work with ALL files or SPECIFIC files
       - Note file format preferences (Excel, PDF, CSV, etc.)
    
    2. ROUTING LOGIC:
      - If the request explicitly mentions **"dataset"**, **"database"**, or **"table"**,
        or asks for specific data retrieval or filtering (e.g., "get", "show", "fetch", "list", "count", "find") → route to **query** unless if the "Database data" is AVAILABLE.
      - If research data IS available → do NOT send to researcher again.
      - If research data is NOT available and request requires external information → researcher.
      - If database data IS available → do NOT send to query agent again (unless a new query is requested).
      - If user attached file data IS available:
        * For analysis/summary requests (keywords: analyze, summarize, extract, insights, explain, interpret) → summary.
        * For visualization requests (keywords: chart, plot, graph, visualize, trend, dashboard):
          - Line chart keywords: line chart, time series, trend over time, temporal data → line_chart.
          - Bar chart keywords: bar chart, comparison, categories, ranking, distribution → bar_chart.
        * For file-specific questions with clear file references → summary.
      - If no file data and simple question → chat.
      - If complex question without files → researcher then summary.
    
    3. SPECIAL HANDLING:
       - If user mentions specific file types or positions ("the Excel file", "PDF only") → pass this context to chosen agent
       - If request is ambiguous about which files to use → default to summary for clarification
       - When all processing complete → END
    
    Respond with ONLY the next agent name: researcher, summary, chat, line_chart, bar_chart, query or END.
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
