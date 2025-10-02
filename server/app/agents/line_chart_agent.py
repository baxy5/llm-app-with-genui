import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.line_chart_model import ChartConfig
from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class LineChartAgent:
  def __init__(self, env_config: EnvConfigService):
    self.env_config = env_config
    self.llm = ChatOpenAI(
      model="gpt-4o-mini",
      api_key=env_config.OPENAI_API_KEY,
    )
    self.llm_with_structured_output = self.llm.with_structured_output(method="json_mode")

  async def chart(self, state: MultiAgentState):
    last_message = state["messages"][-1].content

    system_prompt = """
    You are an expert data analyst and line chart maker. 
    Your task is to analyze the user request and the provided research data from the user, 
    and generate a line chart configuration in JSON format.
    
    Respond with ONLY a JSON object that follows the ECharts configuration format.
    
    Important:
    - The title of the line chart must be maximum 20 characters.
    
    **Example Line Chart Output:**
    {
        "title": {
            "text": "Line chart"
        },
        "toolbox": {
            "feature": {
                "saveAsImage": {}
            }
        },
        "xAxis": {
            "type": "category",
            "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        },
        "yAxis": {
            "type": "value",
            "name": "Revenue (in billions USD)",
            "axisLabel": {
              "formatter": "{value} B"
          }
        },
        "tooltip": {
          "trigger": "axis"
        },
        "series": [
            {
                "data": [150, 230, 224, 218, 135, 147, 260],
                "type": "line"
            }
        ]
    }
    """

    line_chart_messages = [
      SystemMessage(content=system_prompt),
      HumanMessage(
        content=f"""
      User request: {last_message}
      
      Research data: {state["research_data"]}
      """
      ),
    ]

    try:
      response = await self.llm_with_structured_output.ainvoke(line_chart_messages)

      try:
        # Validate the response and save to the messages state
        validated_response = ChartConfig.model_validate(response)
        validated_dict = validated_response.model_dump()

        chart_message = AIMessage(content=json.dumps(validated_dict))

        return {"messages": [chart_message], "current_agent": "END"}
      except Exception as e:
        print(f"Model validation failed. {e}")
        return {"messages": [], "current_agent": "END"}
    except Exception as e:
      print(f"Line chart generation failed. {e}")
      return {"messages": [], "current_agent": "END"}
