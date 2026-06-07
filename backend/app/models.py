from pydantic import BaseModel


class SeriesPoint(BaseModel):
    date: str
    value: float
    sma7: float | None = None
    sma14: float | None = None
    anomaly: bool = False


class MetricSummary(BaseModel):
    average: float
    max_value: float
    max_date: str
    min_value: float
    min_date: str
    compliance_pct: float
    trend_per_year: float
    previous_delta_pct: float | None = None
    quality_label: str
    quality_score: int


class StationSummary(BaseModel):
    name: str
    value: float
    category: str
    color: str


class CriticalDay(BaseModel):
    date: str
    value: float
    delta_pct: float
    category: str


class HeatmapData(BaseModel):
    days: list[str]
    hours: list[str]
    z: list[list[float]]


class MeasurementsResponse(BaseModel):
    city: str
    country: str
    parameter: str
    parameter_label: str
    unit: str
    days: int
    who_limit: float
    source: str
    source_note: str | None = None
    updated_at: str
    series: list[SeriesPoint]
    metrics: MetricSummary
    stations: list[StationSummary]
    critical_days: list[CriticalDay]
    heatmap: HeatmapData
