import json
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.bar_chart_model import ChartConfig
from app.models.state_model import MultiAgentState
from app.services.env_config_service import EnvConfigService

logger = logging.getLogger(__name__)


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
    You are an expert data analyst and bar chart visualization specialist.
    Your task is to create bar charts from user's specific data requests for categorical comparisons.
    
    DATA SOURCE IDENTIFICATION:
    1. ANALYZE USER REQUEST: Look for specific file or data references (e.g., "bar chart from Excel", "compare categories from PDF data")
    2. IDENTIFY RELEVANT DATA: If user specifies a particular file type, focus ONLY on that data source
    3. EXTRACT CATEGORICAL DATA: Look for categories/labels and their corresponding numerical values
    4. HANDLE MULTIPLE FILES: If user doesn't specify, use the most appropriate data for bar chart visualization
    
    DATA PROCESSING RULES:
    - Prioritize categorical data (products, regions, departments, etc.) for X-axis
    - Use numerical values for Y-axis (sales, counts, percentages, amounts)
    - If multiple datasets available, choose based on user's explicit request
    - When user says "chart the Excel file" - use ONLY Excel data, ignore other files
    - Look for column headers to identify categories and values
    - Perfect for comparisons, rankings, and distributions
    
    CHART REQUIREMENTS:
    - Title: Maximum 20 characters, descriptive of the data being compared
    - Use different colors for visual distinction when beneficial
    - Include proper axis labels and value formatting
    - Add tooltips for data clarity
    - Optimize bar width for readability
    
    RESPONSE FORMAT:
    Respond with ONLY a JSON object following ECharts configuration format.
    
    **Example Bar Chart Output:**
    {
        "title": {
            "text": "Sales by Region"
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
            "data": ["North", "South", "East", "West", "Central"]
        },
        "yAxis": {
            "type": "value",
            "name": "Sales ($K)",
            "axisLabel": {
                "formatter": "${value}K"
            }
        },
        "series": [
            {
            "name": "Sales",
            "data": [
                120,
                {
                "value": 200,
                "itemStyle": {
                    "color": "#ff6b6b"
                  }
                },
                150,
                180,
                90
            ],
            "type": "bar",
            "barWidth": "60%"
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
        
        User file attachment data: {state["attachment_contents"]}
        """
      ),
    ]

    try:
      logger.debug("Generating bar chart response.")
      response = await self.llm_with_structured_output.ainvoke(bar_chart_messages)

      try:
        # Validate the response and save to the messages state
        validated_response = ChartConfig.model_validate(response)
        validated_dict = validated_response.model_dump()

        chart_message = AIMessage(content=json.dumps(validated_dict))

        return {"messages": [chart_message], "current_agent": "END"}
      except Exception as e:
        logger.error(f"Bar chart model validation failed: {e}")
        return {"messages": [], "current_agent": "END"}
    except Exception as e:
      logger.error(f"Bar chart generation failed: {e}")
      return {"messages": [], "current_agent": "END"}
