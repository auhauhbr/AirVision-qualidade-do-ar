from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib

import numpy as np
import pandas as pd

PARAMETERS = {
    "pm25": {"label": "PM2.5", "unit": "µg/m³", "who_limit": 15.0},
    "pm10": {"label": "PM10", "unit": "µg/m³", "who_limit": 45.0},
    "no2": {"label": "NO₂", "unit": "µg/m³", "who_limit": 25.0},
    "o3": {"label": "O₃", "unit": "µg/m³", "who_limit": 100.0},
    "co": {"label": "CO", "unit": "mg/m³", "who_limit": 4.0},
    "so2": {"label": "SO₂", "unit": "µg/m³", "who_limit": 40.0},
}

DAY_NAMES = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]


def normalize_parameter(parameter: str) -> str:
    return parameter.lower().replace(".", "").replace("_", "")


def category_for_value(value: float, limit: float) -> tuple[str, str]:
    if value <= limit:
        return "Bom", "#15803D"
    if value <= limit * 2.35:
        return "Moderado", "#B45309"
    return "Ruim", "#DC2626"


def quality_score(value: float, limit: float) -> int:
    return int(max(0, min(100, round((value / max(limit * 2.5, 1)) * 100))))


def build_demo_daily(city: str, parameter: str, days: int) -> pd.DataFrame:
    config = PARAMETERS[parameter]
    seed = int(hashlib.sha256(f"{city}:{parameter}:{days}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    today = datetime.now(timezone.utc).date()
    dates = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    base = config["who_limit"] * (0.8 if parameter in {"pm25", "pm10"} else 0.65)
    values = []
    for idx, day in enumerate(dates):
        seasonal = np.sin(idx / max(days, 1) * np.pi * 2) * config["who_limit"] * 0.18
        weekday = config["who_limit"] * (0.12 if day.weekday() in {0, 1, 2, 3, 4} else -0.05)
        noise = rng.normal(0, config["who_limit"] * 0.17)
        spike = config["who_limit"] * rng.uniform(0.8, 1.7) if idx in {max(3, days // 3), max(4, days // 3 * 2)} else 0
        values.append(max(0.2, round(base + seasonal + weekday + noise + spike, 1)))
    return pd.DataFrame(
        {
            "date": pd.to_datetime(dates),
            "value": values,
            "station": "Amostra AirVision",
            "sensor_id": 0,
        }
    )


def aggregate_daily(records: list[dict], city: str, parameter: str, days: int) -> pd.DataFrame:
    if not records:
        return build_demo_daily(city, parameter, days)
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.date
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"])
    if df.empty:
        return build_demo_daily(city, parameter, days)
    grouped = df.groupby("date", as_index=False).agg(value=("value", "mean"))
    grouped["station"] = "Média da cidade"
    grouped["sensor_id"] = -1
    grouped["date"] = pd.to_datetime(grouped["date"])
    cutoff = pd.Timestamp(datetime.now(timezone.utc).date() - timedelta(days=days - 1))
    return grouped[grouped["date"] >= cutoff].sort_values("date")


def summarize(df: pd.DataFrame, parameter: str) -> dict:
    config = PARAMETERS[parameter]
    limit = config["who_limit"]
    work = df.copy().sort_values("date")
    work["sma7"] = work["value"].rolling(7, min_periods=3).mean().round(1)
    work["sma14"] = work["value"].rolling(14, min_periods=5).mean().round(1)
    mean = float(work["value"].mean()) if not work.empty else 0.0
    std = float(work["value"].std(ddof=0)) or 0.0
    threshold = max(limit * 2, mean + std * 1.5)
    work["anomaly"] = work["value"] >= threshold

    max_row = work.loc[work["value"].idxmax()]
    min_row = work.loc[work["value"].idxmin()]
    compliance = float((work["value"] <= limit).mean() * 100)
    x = np.arange(len(work))
    slope_daily = float(np.polyfit(x, work["value"], 1)[0]) if len(work) > 1 else 0.0
    trend_per_year = slope_daily * 365
    midpoint = len(work) // 2
    previous_delta = None
    if midpoint > 0:
        previous = float(work.iloc[:midpoint]["value"].mean())
        current = float(work.iloc[midpoint:]["value"].mean())
        previous_delta = round(((current - previous) / previous) * 100, 1) if previous else None
    quality_label, _ = category_for_value(mean, limit)

    critical = work.assign(delta_pct=((work["value"] - mean) / mean * 100).round(0))
    critical = critical.sort_values("value", ascending=False).head(6)

    return {
        "series": [
            {
                "date": row.date.strftime("%Y-%m-%d"),
                "value": round(float(row.value), 1),
                "sma7": None if pd.isna(row.sma7) else round(float(row.sma7), 1),
                "sma14": None if pd.isna(row.sma14) else round(float(row.sma14), 1),
                "anomaly": bool(row.anomaly),
            }
            for row in work.itertuples()
        ],
        "metrics": {
            "average": round(mean, 1),
            "max_value": round(float(max_row["value"]), 1),
            "max_date": max_row["date"].strftime("%Y-%m-%d"),
            "min_value": round(float(min_row["value"]), 1),
            "min_date": min_row["date"].strftime("%Y-%m-%d"),
            "compliance_pct": round(compliance, 0),
            "trend_per_year": round(trend_per_year, 1),
            "previous_delta_pct": previous_delta,
            "quality_label": quality_label,
            "quality_score": quality_score(mean, limit),
        },
        "critical_days": [
            {
                "date": row.date.strftime("%Y-%m-%d"),
                "value": round(float(row.value), 1),
                "delta_pct": round(float(row.delta_pct), 0),
                "category": category_for_value(float(row.value), limit)[0],
            }
            for row in critical.itertuples()
        ],
    }


def station_summaries(records: list[dict], df: pd.DataFrame, parameter: str) -> list[dict]:
    limit = PARAMETERS[parameter]["who_limit"]
    if records:
        raw = pd.DataFrame(records)
        raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
        latest = raw.dropna(subset=["value"]).sort_values("date").groupby("station", as_index=False).tail(1)
        latest = latest.sort_values("value").head(5)
    else:
        latest = pd.DataFrame(
            {
                "station": ["Boa Viagem", "Afogados", "Olinda", "Paulista", "Santo Amaro"],
                "value": np.linspace(df["value"].mean() * 0.72, df["value"].mean() * 1.35, 5),
            }
        )
    stations = []
    for row in latest.itertuples():
        category, color = category_for_value(float(row.value), limit)
        stations.append({"name": str(row.station), "value": round(float(row.value), 1), "category": category, "color": color})
    return stations


def build_heatmap(df: pd.DataFrame, parameter: str) -> dict:
    limit = PARAMETERS[parameter]["who_limit"]
    hours = [f"{hour:02d}h" for hour in range(24)]
    day_baseline = {i: float(df[df["date"].dt.dayofweek == i]["value"].mean()) for i in range(7)}
    overall = float(df["value"].mean()) if not df.empty else limit
    z = []
    for api_day in [6, 0, 1, 2, 3, 4, 5]:
        baseline = day_baseline.get(api_day)
        if np.isnan(baseline):
            baseline = overall
        row = []
        for hour in range(24):
            rush = 1.0
            if 6 <= hour <= 9:
                rush = 1.28
            elif 17 <= hour <= 20:
                rush = 1.18
            elif 0 <= hour <= 5:
                rush = 0.82
            row.append(round(max(0.1, baseline * rush), 1))
        z.append(row)
    return {"days": DAY_NAMES, "hours": hours, "z": z}
