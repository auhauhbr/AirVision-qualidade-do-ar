from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import requests

from .analytics import normalize_parameter


class OpenAQError(RuntimeError):
    pass


class OpenAQClient:
    def __init__(self, base_url: str, api_key: str | None = None, timeout: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, params=params or {}, timeout=self.timeout)
        except requests.RequestException as exc:
            raise OpenAQError(f"Falha ao conectar na OpenAQ: {exc}") from exc
        if response.status_code in {401, 403}:
            raise OpenAQError("A OpenAQ recusou a requisição. Configure OPENAQ_API_KEY no .env.")
        if response.status_code == 429:
            raise OpenAQError("Limite da OpenAQ atingido. Aguarde a janela de rate limit ou use cache/API key.")
        if not response.ok:
            raise OpenAQError(f"OpenAQ retornou HTTP {response.status_code}: {response.text[:160]}")
        return response.json()

    def parameter_ids(self) -> dict[str, int]:
        payload = self._get("/parameters", {"parameter_type": "pollutant", "limit": 100})
        result: dict[str, int] = {}
        for item in payload.get("results", []):
            name = normalize_parameter(str(item.get("name") or ""))
            if name:
                result[name] = int(item["id"])
        return result

    def locations_nearby(
        self,
        *,
        lat: float,
        lon: float,
        radius: int,
        iso: str,
        parameter_id: int | None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "coordinates": f"{lat:.4f},{lon:.4f}",
            "radius": min(radius, 25000),
            "iso": iso,
            "limit": limit,
            "page": 1,
            "sort_order": "asc",
        }
        if parameter_id:
            params["parameters_id"] = parameter_id
        payload = self._get("/locations", params)
        return list(payload.get("results", []))

    def sensor_days(self, sensor_id: int, date_from: date, date_to: date, limit: int = 1000) -> list[dict[str, Any]]:
        payload = self._get(
            f"/sensors/{sensor_id}/days",
            {"date_from": date_from.isoformat(), "date_to": date_to.isoformat(), "limit": limit, "page": 1},
        )
        return list(payload.get("results", []))


def collect_daily_records(
    client: OpenAQClient,
    *,
    city: str,
    iso: str,
    lat: float,
    lon: float,
    radius: int,
    parameter: str,
    days: int,
) -> tuple[list[dict], list[str]]:
    notes: list[str] = []
    param_ids = client.parameter_ids()
    parameter_id = param_ids.get(parameter)
    if parameter_id is None:
        notes.append(f"Parâmetro {parameter} não encontrado em /v3/parameters; tentando filtrar sensores por nome.")

    locations = client.locations_nearby(lat=lat, lon=lon, radius=radius, iso=iso, parameter_id=parameter_id)
    sensors: list[tuple[int, str]] = []
    for location in locations:
        location_name = location.get("name") or location.get("locality") or city
        for sensor in location.get("sensors", []):
            sensor_param = normalize_parameter(str(sensor.get("parameter", {}).get("name") or ""))
            if sensor_param == parameter and sensor.get("id"):
                sensors.append((int(sensor["id"]), str(location_name)))
    if not sensors:
        raise OpenAQError(f"Nenhum sensor {parameter} encontrado em {city}.")

    today = datetime.now(timezone.utc).date()
    date_from = today - timedelta(days=days - 1)
    records: list[dict] = []
    for sensor_id, station_name in sensors[:8]:
        for row in client.sensor_days(sensor_id, date_from, today, limit=max(100, days + 10)):
            value = row.get("value")
            if value is None and isinstance(row.get("summary"), dict):
                value = row["summary"].get("avg")
            period = row.get("period") or {}
            dt = period.get("datetimeFrom") or period.get("datetimeTo") or {}
            timestamp = dt.get("local") or dt.get("utc")
            if value is None or timestamp is None:
                continue
            records.append(
                {
                    "date": timestamp,
                    "value": value,
                    "station": station_name,
                    "sensor_id": sensor_id,
                }
            )
    if not records:
        raise OpenAQError(f"Sensores encontrados em {city}, mas sem dados diários recentes para {parameter}.")
    return records, notes
