import logging

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService

logger = logging.getLogger(__name__)


class ResearchAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.tools = [self._create_tavily_tool()]
    self.llm = ChatOpenAI(
      model="gpt-4o",
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
        logger.error(f"Failed to generato tool call: {e}")
        return f"Search error: {str(e)}"

    return tavily_search_tool

  async def research(self, state: MultiAgentState):
    system_message = SystemMessage(
      content=(
        "You are a research agent specialized in gathering external information to complement user data. "
        "IMPORTANT: Your role is to find external/web-based information, NOT to analyze user's uploaded files. "
        "RESEARCH FOCUS GUIDELINES:\n"
        "1. If user asks about topics related to their files but needs external context: Research complementary information\n"
        "2. If user needs current market data, trends, or benchmarks: Search for up-to-date 2025 information\n"
        "3. If user asks for comparisons with industry standards: Find relevant external benchmarks\n"
        "4. If user needs background information about topics mentioned in their files: Research contextual data\n"
        "RESEARCH APPROACH:\n"
        "- Focus on factual, current information from reliable sources\n"
        "- Present findings in clear, structured format (text, lists, tables)\n"
        "- Include numerical data when available (revenue, growth rates, statistics)\n"
        "- Always search for the most recent 2025 data\n"
        "- If exact numbers unavailable, provide best available estimates with source context\n"
        "RESPONSE FORMAT:\n"
        "- Return raw findings in structured text format\n"
        "- Do NOT provide analysis instructions or chart-generation steps\n"
        "- Focus on data that can complement or contextualize user's file content\n"
        "- If no relevant external information found: 'I couldn't find any relevant external information.'\n"
        "Remember: You gather external research data; other agents handle user file analysis."
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
      logger.debug("Generating research response.")
      response = await client_with_tools.ainvoke(research_messages)
      research_messages.append(response)

      # Handle tool calls if present
      final_research_response = ""
      if response.tool_calls:
        logger.debug("Tools were called.")
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
        logger.debug("No tools were called.")
        # No tools were called, use the initial response
        final_research_response = response.content

      return {"research_data": final_research_response, "current_agent": "supervisor"}

    except Exception as e:
      logger.error(f"Failed to generate research response: {e}")
      error_msg = f"Research agent error: {str(e)}"
      return {"research_data": error_msg, "current_agent": "supervisor"}
