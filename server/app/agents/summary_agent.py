from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class SummaryAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.llm = ChatOpenAI(
      model="gpt-4o",
      api_key=env_config.OPENAI_API_KEY,
    )

  async def summary(self, state: MultiAgentState):
    last_message = state["messages"][-1].content

    system_prompt = SystemMessage(
      content=(
        "You are an expert data analyst and summarizer. Your task is to provide detailed, accurate analysis based on the user's specific request. "
        "CRITICAL: Pay close attention to which files or data sources the user wants you to focus on. "
        "SELECTIVE FILE PROCESSING RULES:\n"
        "1. If user specifies a particular file type (e.g., 'Excel file', 'PDF document', 'CSV data'): ONLY use that file type's content\n"
        "2. If user mentions file position (e.g., 'first file', 'second attachment'): Focus on that specific file\n"
        "3. If user says 'summarize the Excel file' and multiple files are attached: Extract and use ONLY Excel file content\n"
        "4. If no specific file mentioned but multiple files available: Clearly indicate which file(s) you're analyzing\n"
        "5. If user asks about 'all files' or 'everything': Process all available content\n"
        "CONTENT IDENTIFICATION:\n"
        "- Look for file type indicators in the attachment data (Sheet names = Excel, page structure = PDF, etc.)\n"
        "- When multiple files present, clearly separate your analysis by file type\n"
        "- Always mention which specific file(s) you're summarizing in your response\n"
        "OUTPUT REQUIREMENTS:\n"
        "- Structure your summary with clear headings when dealing with multiple sources\n"
        "- Highlight key findings, important details, and actionable insights\n"
        "- Avoid speculation - only use information present in the specified data\n"
        "- If requested file type is not available, clearly state this limitation\n"
        "- Start your response by confirming which file(s) you're analyzing"
      )
    )

    user_message = HumanMessage(content=f"User request: {last_message}")
    research_message = HumanMessage(content=f"Research data: {state['research_data']}")
    attachment_contents_message = HumanMessage(
      content=f"User file attachment data: {state['attachment_contents']}"
    )

    summary_messages = [system_prompt, user_message, research_message, attachment_contents_message]

    try:
      response = await self.llm.ainvoke(summary_messages)

      return {
        "messages": [response],
        "current_agent": "END",
      }
    except Exception as e:
      error_msg = f"Summary agent error: {str(e)}"
      return {"summary_data": error_msg, "current_agent": "END"}
