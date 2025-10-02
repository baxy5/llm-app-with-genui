from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class ResearchAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.tools = [self._create_tavily_tool()]
    self.llm = ChatOpenAI(
      model="gpt-4o-mini",
      api_key=env_config.OPENAI_API_KEY,
    )

  def _create_tavily_tool(self):
    @tool
    async def tavily_search_tool(input: str) -> str:
      """Web search tool for gathering information."""
      try:
        tool = TavilySearch(api_key=self.env_config.TAVILY_API_KEY, max_results=1)
        result = tool.invoke(input)
        return result["results"][0]["content"]
      except Exception as e:
        return f"Search error: {str(e)}"

    return tavily_search_tool

  async def research(self, state: MultiAgentState):
    system_message = SystemMessage(
      content=(
        "You are a research agent. Use the search tool to gather accurate and comprehensive information "
        "about the user's query. Always focus on returning the raw findings in a clear and structured format "
        "(such as text, lists, tables, or JSON-like blocks). "
        "Do not provide instructions, code, or chart-generation steps. "
        "If the data is numerical (e.g., yearly revenue, growth rates, statistics), present it clearly as text or in a simple table. "
        "If exact numbers are unavailable, summarize the best available estimates with sources. "
        "Your final response must always be textual. "
        "If you cannot find reliable information, reply with: 'I couldn't find any information.'"
      )
    )

    client_with_tools = self.llm.bind_tools(self.tools)

    # Ensure we have the user input
    if not state.get("messages") or len(state["messages"]) == 0:
      error_msg = "No user input found in state"
      state["research_data"] = error_msg
      state["current_agent"] = "supervisor"
      return state

    tool_map = {tool.name: tool for tool in self.tools}

    research_messages = [system_message] + [state["messages"][-1]]

    try:
      response = await client_with_tools.ainvoke(research_messages)
      research_messages.append(response)

      # Handle tool calls if present
      final_research_response = ""
      if response.tool_calls:
        for tool_call in response.tool_calls:
          if tool_call["name"] in tool_map:
            tool = tool_map[tool_call["name"]]
            tool_result = await tool.ainvoke(tool_call["args"])

            # Add tool result to messages
            tool_message = ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
            research_messages.append(tool_message)

        # Get final response after tool execution
        final_response = await client_with_tools.ainvoke(research_messages)
        final_research_response = final_response.content
      else:
        # No tools were called, use the initial response
        final_research_response = response.content

      return {"research_data": final_research_response, "current_agent": "supervisor"}

    except Exception as e:
      error_msg = f"Research agent error: {str(e)}"
      return {"research_data": error_msg, "current_agent": "supervisor"}
