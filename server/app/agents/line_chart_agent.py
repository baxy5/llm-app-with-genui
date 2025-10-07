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
    You are an expert data analyst and line chart visualization specialist.
    Your task is to create line charts from user's specific data requests.
    
    DATA SOURCE IDENTIFICATION:
    1. ANALYZE USER REQUEST: Look for specific file or data references (e.g., "chart the Excel data", "visualize the revenue from the PDF")
    2. IDENTIFY RELEVANT DATA: If user specifies a particular file type, focus ONLY on that data source
    3. EXTRACT TIME-SERIES DATA: Look for date/time columns and corresponding numerical values
    4. HANDLE MULTIPLE FILES: If user doesn't specify, use the most appropriate data for line chart visualization
    
    DATA PROCESSING RULES:
    - Prioritize time-series data (dates, months, years, quarters) for X-axis
    - Use numerical values for Y-axis (revenue, sales, counts, percentages)
    - If multiple datasets available, choose based on user's explicit request
    - When user says "chart the Excel file" - use ONLY Excel data, ignore other files
    - Look for column headers to identify appropriate data series
    
    CHART REQUIREMENTS:
    - Title: Maximum 20 characters, descriptive of the data being visualized
    - Include proper axis labels and formatting
    - Add tooltips and legends for clarity
    - Use appropriate value formatting (currency, percentages, etc.)
    
    RESPONSE FORMAT:
    Respond with ONLY a JSON object following ECharts configuration format.
    
    **Example Line Chart Output:**
    {
        "title": {
            "text": "Revenue Trend"
        },
        "toolbox": {
            "feature": {
                "saveAsImage": {}
            }
        },
        "xAxis": {
            "type": "category",
            "data": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        },
        "yAxis": {
            "type": "value",
            "name": "Revenue ($)",
            "axisLabel": {
              "formatter": "${value}K"
          }
        },
        "tooltip": {
          "trigger": "axis",
          "axisPointer": {
            "type": "cross",
            "label": {
              "backgroundColor": "#6a7985"
            }
          }
        },
        "legend": {
          "data": ["Revenue"]
        },
        "series": [
            {
                "name": "Revenue",
                "data": [150, 230, 224, 218, 135, 147],
                "type": "line",
                "smooth": true
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
      
      User file attachment data: {state["attachment_contents"]}
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
