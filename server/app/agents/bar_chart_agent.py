import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.bar_chart_model import ChartConfig
from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService


class BarChartAgent:
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
    You are an expert data analyst and bar chart maker. 
    Your task is to analyze the user request and the provided research data from the user, 
    and generate a line chart configuration in JSON format.
    
    Respond with ONLY a JSON object that follows the ECharts configuration format.
    
    Important:
    - The title of the bar chart must be maximum 20 characters.
    - If it's needed define different colors for each bar using the itemStyle.
    
    **Example Bar Chart Output:**
    {
        "title": {
            "text": "Bar chart"
        },
        "toolbox": {
            "feature": {
                "saveAsImage": {}
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "xAxis": {
            "type": "category",
            "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        },
        "yAxis": {
            "type": "value"
        },
        "series": [
            {
            "name": "Beer",
            "data": [
                120,
                {
                "value": 200,
                "itemStyle": {
                    "color": "#505372"
                  }
                },
                150,
                80,
                70,
                110,
                130
            ],
            "type": "bar",
            "barWidth": "10%"
            }
        ]
    }
    """

    bar_chart_messages = [
      SystemMessage(content=system_prompt),
      HumanMessage(
        content=f"""
        User request: {last_message}
        
        Research data: {state["research_data"]}
        """
      ),
    ]

    try:
      response = await self.llm_with_structured_output.ainvoke(bar_chart_messages)

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
