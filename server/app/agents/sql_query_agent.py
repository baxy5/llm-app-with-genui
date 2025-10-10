from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class SqlQueryAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.llm = ChatOpenAI(
      model="gpt-4o-mini",
      api_key=env_config.OPENAI_API_KEY,
    )

  async def generate(self, state: MultiAgentState):
    last_message = state["messages"][-1].content

    system_message = SystemMessage(
      content=(
        "You are an expert PostgreSQL query generator. "
        "Your task is to interpret natural language user requests and produce a single, safe, and executable SQL query "
        "that retrieves the requested data from the existing database.\n\n"
        "### Database schema:\n"
        "Table name: dataset\n"
        "Columns:\n"
        "  - id (INTEGER, primary key)\n"
        "  - product_name (STRING, not null)\n"
        "  - year (STRING, not null)\n"
        "  - month (STRING, not null)\n"
        "  - revenue (INTEGER, not null)\n"
        "  - expenses (INTEGER, not null)\n"
        "  - current_employees (INTEGER, not null)\n\n"
        "### Rules:\n"
        "1. Always use **only** the 'dataset' table. Do not reference any other tables or databases.\n"
        "2. Generate only **valid PostgreSQL SQL** syntax that can be executed directly.\n"
        "3. Output only the SQL query — no explanations, reasoning, comments, or markdown formatting.\n"
        "4. Ensure every query is safe (no data modification statements such as INSERT, UPDATE, DELETE, or DROP).\n"
        "5. If the user request is ambiguous, generate the most reasonable SELECT query based on the table schema.\n"
        "6. Do not apply any LIMIT clause unless the user explicitly asks for limited results.\n"
        "7. Support filtering, aggregation (SUM, AVG, COUNT, etc.), grouping, and ordering if requested.\n"
        "8. Use appropriate column names exactly as defined in the schema.\n"
        "9. Return all relevant rows and columns that match the user's intent.\n\n"
        "10. If the user request is unrelated to this database or cannot be reasonably expressed as an SQL query, "
        "respond exactly with the text: 'False'.\n\n"
        "### Example behavior:\n"
        "User: show total revenue by year\n"
        "Output: SELECT year, SUM(revenue) AS total_revenue FROM dataset GROUP BY year;\n\n"
        "User: get all data for 2024\n"
        "Output: SELECT * FROM dataset WHERE year = '2024';\n\n"
        "User: show product names and expenses where revenue is greater than 10000\n"
        "Output: SELECT product_name, expenses FROM dataset WHERE revenue > 10000;"
      )
    )

    """ system_message = SystemMessage(
      content=(
        "You are a PostgreSQL expert. Generate a single safe, executable SQL query from the user's request "
        "using only the table below.\n\n"
        "Table: dataset\n"
        "Columns: id (int), product_name (string), year (string), month (string), "
        "revenue (int), expenses (int), current_employees (int)\n\n"
        "Rules:\n"
        "- Use only the 'dataset' table.\n"
        "- Output only SQL, no explanations or markdown.\n"
        "- Produce only SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.).\n"
        "- Use valid PostgreSQL syntax.\n"
        "- No LIMIT unless the user asks for it.\n"
        "- Support filters, GROUP BY, ORDER BY, and aggregates.\n"
        "- Use exact column names.\n"
        "- If the request cannot be expressed as an SQL query for this table, output exactly: False.\n\n"
        "Examples:\n"
        "User: show total revenue by year\n"
        "Output: SELECT year, SUM(revenue) AS total_revenue FROM dataset GROUP BY year;\n"
        "User: get all data for 2024\n"
        "Output: SELECT * FROM dataset WHERE year = '2024';\n"
        "User: what's your name?\n"
        "Output: False"
      )
    ) """

    message = HumanMessage(
      content=f"""
    User query: {last_message}
    """
    )

    messages = [system_message] + [message]

    try:
      response = await self.llm.ainvoke(messages)
      print("SqlQuery: ", response)

      return {"database_query": response.content, "current_agent": "supervisor"}
    except Exception as e:
      print(f"SqlQueryAgent -> response generation failed: {e}")
      return {"messages": [], "current_agent": "END"}
