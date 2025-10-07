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
        content=(
          "You are a helpful assistant specialized in answering questions and providing direct support. "
          "FILE-AWARE RESPONSES:\n"
          "- If user references specific files in their question, acknowledge which files you can access\n"
          "- When user asks about file content, provide direct answers based on available data\n"
          "- If asked about specific file types (Excel, PDF, etc.), focus your response on that content\n"
          "- Clearly state if requested file information is not available\n"
          "CONVERSATION HANDLING:\n"
          "- Answer direct questions concisely and accurately\n"
          "- Provide helpful explanations for technical or complex topics\n"
          "- If question requires analysis beyond simple Q&A, suggest appropriate next steps\n"
          "- Handle general conversation, requirements gathering, and clarifications\n"
          "RESPONSE STYLE:\n"
          "- Be conversational but informative\n"
          "- Reference specific file content when relevant to the question\n"
          "- Offer to help with further analysis if user needs deeper insights\n"
          "- Keep responses focused and avoid unnecessary elaboration"
        )
      )
      messages = [system_message] + list(messages)

    try:
      response = await self.llm.ainvoke(messages)

      return {"messages": [response], "current_agent": "END"}
    except Exception:
      return {"messages": [], "current_agent": "END"}
