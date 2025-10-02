from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class SummaryAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.llm = ChatOpenAI(
      model="gpt-4o-mini",
      api_key=env_config.OPENAI_API_KEY,
    )

  async def summary(self, state: MultiAgentState):
    last_message = state["messages"][-1].content

    system_prompt = SystemMessage(
      content=(
        "You are an expert summarizer. Your task is to write a detailed, accurate, and clear summary based on the provided research data and the user's question. "
        "Carefully read the research data and address all relevant points from the user's question. "
        "Your summary should be concise yet comprehensive, highlighting key findings, important details, and actionable insights. "
        "Avoid speculation and only use information present in the research data. "
        "Structure your summary in well-organized paragraphs for readability."
      )
    )

    user_message = HumanMessage(content=f"User request: {last_message}")
    research_message = HumanMessage(content=f"Research data: {state['research_data']}")

    summary_messages = [system_prompt, user_message, research_message]

    try:
      response = await self.llm.ainvoke(summary_messages)

      return {
        "messages": [response],
        "current_agent": "END",
      }
    except Exception as e:
      error_msg = f"Summary agent error: {str(e)}"
      return {"summary_data": error_msg, "current_agent": "END"}
