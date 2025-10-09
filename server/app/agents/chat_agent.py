from langchain_core.messages import HumanMessage, SystemMessage
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
    research_message = None

    if state.get("research_data"):
      research_message = HumanMessage(content=f"Research data:\n\n {state['research_data']}")

    # Add system message only if it's the first interaction
    if not messages or not any(isinstance(msg, SystemMessage) for msg in messages):
      system_message = SystemMessage(
        content=(
          "You are a helpful, file-aware assistant specialized in answering questions and providing direct support.\n"
          "\n"
          "IMPORTANT RULES:\n"
          "1. Never mention your training data or knowledge cutoff.\n"
          "2. If no relevant information or files are available, respond briefly with: 'I couldn’t find relevant information.'\n"
          "\n"
          "FILE-AWARE RESPONSES:\n"
          "- When the user references files, acknowledge which files you can access.\n"
          "- Answer based only on available content—no assumptions or outside information.\n"
          "- If a requested file type or content is missing, say so clearly.\n"
          "\n"
          "CONVERSATION HANDLING:\n"
          "- Answer questions concisely and accurately.\n"
          "- Provide clear explanations for technical or complex topics.\n"
          "- If deeper analysis is needed, suggest next steps or refer to the summary agent.\n"
          "\n"
          "RESPONSE STYLE:\n"
          "- Be conversational but informative.\n"
          "- Reference file content when relevant.\n"
          "- Keep responses short, relevant, and avoid filler text.\n"
        )
      )

      messages = [system_message] + list(messages)

    if research_message:
      messages = messages + [research_message]

    try:
      response = await self.llm.ainvoke(messages)

      return {"messages": [response], "current_agent": "END"}
    except Exception:
      return {"messages": [], "current_agent": "END"}
