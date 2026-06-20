from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .analytics import (
    PARAMETERS,
    aggregate_daily,
    build_demo_daily,
    build_heatmap,
    normalize_parameter,
    station_summaries,
    summarize,
)
from .cache import SQLiteCache
from .cities import COUNTRY_LABELS, CITY_PRESETS, get_city_config
from .config import get_settings
from .models import MeasurementsResponse
from .openaq import OpenAQClient, OpenAQError, collect_daily_records

app = FastAPI(
    title="AirVision API",
    description="API FastAPI para análise de qualidade do ar com dados OpenAQ.",
    version="0.1.0",
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


def build_payload(
    *,
    country: str,
    city: str,
    parameter: str,
    days: int,
    records: list[dict],
    source: Literal["openaq", "demo", "cache"],
    source_note: str | None = None,
) -> dict:
    df = aggregate_daily(records, city, parameter, days) if records else build_demo_daily(city, parameter, days)
    summary = summarize(df, parameter)
    config = PARAMETERS[parameter]
    return {
        "city": city,
        "country": COUNTRY_LABELS.get(country, country),
        "parameter": parameter,
        "parameter_label": config["label"],
        "unit": config["unit"],
        "days": days,
        "who_limit": config["who_limit"],
        "source": source,
        "source_note": source_note,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "series": summary["series"],
        "metrics": summary["metrics"],
        "stations": station_summaries(records, df, parameter),
        "critical_days": summary["critical_days"],
        "heatmap": build_heatmap(df, parameter),
    }


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "service": "AirVision API"}


@app.get("/api/options")
def options() -> dict:
    return {
        "countries": [{"code": code, "name": COUNTRY_LABELS.get(code, code)} for code in CITY_PRESETS],
        "cities": CITY_PRESETS,
        "parameters": [
            {"value": key, "label": f"{item['label']} - {item['unit']}", "who_limit": item["who_limit"]}
            for key, item in PARAMETERS.items()
        ],
        "periods": [7, 30, 90, 365],
    }


@app.get("/api/measurements", response_model=MeasurementsResponse)
def measurements(
    city: str = Query(default="Recife"),
    country: str = Query(default="BR", min_length=2, max_length=2),
    parameter: str = Query(default="pm25"),
    days: int = Query(default=30, ge=7, le=365),
) -> dict:
    country = country.upper()
    parameter = normalize_parameter(parameter)
    if parameter not in PARAMETERS:
        raise HTTPException(status_code=400, detail=f"Parâmetro inválido: {parameter}")
    try:
        city_config = get_city_config(country, city)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    settings = get_settings()
    cache = SQLiteCache(settings.db_path, settings.cache_ttl_minutes)
    cache_key = f"{country}:{city}:{parameter}:{days}"
    cached = cache.get(cache_key)
    if cached:
        cached["source"] = "cache"
        return cached

    records: list[dict] = []
    source = "openaq"
    source_note: str | None = None
    try:
        client = OpenAQClient(settings.openaq_base_url, settings.openaq_api_key)
        records, notes = collect_daily_records(
            client,
            city=city,
            iso=country,
            lat=city_config["lat"],
            lon=city_config["lon"],
            radius=city_config["radius"],
            parameter=parameter,
            days=days,
        )
        if notes:
            source_note = " ".join(notes)
    except OpenAQError as exc:
        source = "demo"
        source_note = f"Modo demonstração: {exc}"

    payload = build_payload(
        country=country,
        city=city,
        parameter=parameter,
        days=days,
        records=records,
        source=source,
        source_note=source_note,
    )
    if source == "openaq":
        cache.set(cache_key, payload)
    return payload


@app.get("/{full_path:path}")
def serve_frontend(full_path: str) -> FileResponse:
    index_path = FRONTEND_DIST / "index.html"
    if not index_path.exists() or full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(index_path)
