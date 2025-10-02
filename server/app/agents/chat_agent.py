from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class ChatAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.llm = ChatOpenAI(
      model="gpt-4o-mini",
      api_key=env_config.OPENAI_API_KEY,
    )

  async def chat(self, state: MultiAgentState):
    messages = state["messages"]

    # Add system message only if it's the first interaction
    if not messages or not any(isinstance(msg, SystemMessage) for msg in messages):
      system_message = SystemMessage(
        "You are a helpful assistant, your task is to answer the user's questions."
      )
      messages = [system_message] + list(messages)

    try:
      response = await self.llm.ainvoke(messages)

      return {"messages": [response], "current_agent": "END"}
    except Exception:
      return {"messages": [], "current_agent": "END"}
