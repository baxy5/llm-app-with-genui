from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field, field_validator


class Title(BaseModel):
  text: str


class ToolboxFeature(BaseModel):
  saveAsImage: Dict[str, Any] = {}


class Toolbox(BaseModel):
  feature: ToolboxFeature


class XAxis(BaseModel):
  type: str = Field(default="category", description="Axis type")
  data: List[str] = Field(default_factory=list, description="Axis data")

  @field_validator("type", mode="before")
  @classmethod
  def validate_type(cls, v):
    if v is None:
      return "category"

    # Only allow valid eChart types
    valid_types = ["category", "value", "time", "log"]
    cleaned_type = str(v).lower().strip()
    return cleaned_type if cleaned_type in valid_types else "category"

  @field_validator("data", mode="before")
  @classmethod
  def clean_data(cls, v):
    if not v or v is None:
      return []

    # Filter out None/null values and convert to strings
    cleaned_data = []
    for item in v:
      if item is not None and str(item).strip():
        cleaned_data.append(str(item).strip())

    return cleaned_data


class AxisLabel(BaseModel):
  formatter: str = Field(default=None, description="Formatter for axis labels (e.g. '{value} B').")


class YAxis(BaseModel):
  type: str = Field(default="value", description="Axis type")
  name: str = Field(default=None, description="Axis label name (e.g. 'Revenue (in billions USD)')")
  axisLabel: AxisLabel = Field(default=None, description="Axis label configuration")

  @field_validator("type", mode="before")
  @classmethod
  def validate_type(cls, v):
    if v is None:
      return "value"
    valid_types = ["category", "value", "time", "log"]
    cleaned_type = str(v).lower().strip()
    return cleaned_type if cleaned_type in valid_types else "value"


class AxisPointerLabel(BaseModel):
  backgroundColor: str = Field(description="Background color for axis pointer label")


class AxisPointer(BaseModel):
  type: str = Field(default="cross", description="Axis pointer type")
  label: AxisPointerLabel = Field(
    default_factory=AxisPointerLabel, description="Label configuration for axis pointer"
  )


class Tooltip(BaseModel):
  trigger: str = Field(default="axis", description="Tooltip trigger type")
  axisPointer: AxisPointer = Field(
    default_factory=AxisPointer, description="Axis pointer configuration"
  )


class SeriesItem(BaseModel):
  data: List[Union[int, float]] = Field(default_factory=list, description="Series data")
  type: str = Field(default="bar", description="Chart type")

  @field_validator("type", mode="before")
  @classmethod
  def validate_type(cls, v):
    if v is None:
      return "bar"
    valid_types = ["line"]
    cleaned_type = str(v).lower().strip()
    return cleaned_type if cleaned_type in valid_types else "line"

  @field_validator("data", mode="before")
  @classmethod
  def clean_data(cls, v):
    if not v or v is None:
      return []

    cleaned_data = []
    for item in v:
      if item is None:
        cleaned_data.append(0)
      else:
        try:
          cleaned_data.append(float(item))
        except (ValueError, TypeError):
          cleaned_data.append(0)

    return cleaned_data


class ChartConfig(BaseModel):
  title: Title
  toolbox: Toolbox
  xAxis: XAxis
  yAxis: YAxis
  tooltip: Tooltip
  series: List[SeriesItem]
