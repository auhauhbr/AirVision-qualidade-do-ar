const LIMITS = {
  pm25: { label: "PM2.5", unit: "µg/m³", limit: 15 },
  pm10: { label: "PM10", unit: "µg/m³", limit: 45 },
  no2: { label: "NO₂", unit: "µg/m³", limit: 25 },
  o3: { label: "O₃", unit: "µg/m³", limit: 100 },
  co: { label: "CO", unit: "mg/m³", limit: 4 },
  so2: { label: "SO₂", unit: "µg/m³", limit: 40 },
};

const COUNTRY_NAMES = {
  BR: "Brasil",
  AR: "Argentina",
  PT: "Portugal",
  US: "Estados Unidos",
};

function seededValue(seed) {
  const value = Math.sin(seed * 12.9898) * 43758.5453;
  return value - Math.floor(value);
}

function movingAverage(values, size, index) {
  if (index < Math.min(size - 1, 2)) {
    return null;
  }
  const start = Math.max(0, index - size + 1);
  const selection = values.slice(start, index + 1);
  return Number((selection.reduce((sum, value) => sum + value, 0) / selection.length).toFixed(1));
}

export function createDemoMeasurements(filters) {
  const config = LIMITS[filters.parameter] || LIMITS.pm25;
  const dates = [];
  const values = [];
  const now = new Date();

  for (let index = filters.days - 1; index >= 0; index -= 1) {
    const date = new Date(now);
    date.setDate(now.getDate() - index);
    const position = filters.days - index;
    const base = config.limit * 0.82;
    const seasonal = Math.sin(position / 4.2) * config.limit * 0.18;
    const noise = (seededValue(position + filters.city.length) - 0.42) * config.limit * 0.55;
    const spike = position === Math.floor(filters.days * 0.38) || position === Math.floor(filters.days * 0.72)
      ? config.limit * 1.25
      : 0;
    dates.push(date.toISOString().slice(0, 10));
    values.push(Number(Math.max(0.2, base + seasonal + noise + spike).toFixed(1)));
  }

  const average = values.reduce((sum, value) => sum + value, 0) / values.length;
  const maxValue = Math.max(...values);
  const minValue = Math.min(...values);
  const maxIndex = values.indexOf(maxValue);
  const minIndex = values.indexOf(minValue);
  const anomalyLimit = Math.max(config.limit * 2, average * 1.65);
  const compliance = (values.filter((value) => value <= config.limit).length / values.length) * 100;
  const trend = values.length > 1 ? ((values.at(-1) - values[0]) / values.length) * 365 : 0;
  const qualityLabel = average <= config.limit ? "Bom" : average <= config.limit * 2.35 ? "Moderado" : "Ruim";

  const series = values.map((value, index) => ({
    date: dates[index],
    value,
    sma7: movingAverage(values, 7, index),
    sma14: movingAverage(values, 14, index),
    anomaly: value >= anomalyLimit,
  }));

  const criticalDays = series
    .map((point) => ({
      date: point.date,
      value: point.value,
      delta_pct: Math.round(((point.value - average) / average) * 100),
      category: point.value <= config.limit ? "Bom" : point.value <= config.limit * 2.35 ? "Moderado" : "Ruim",
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);

  const hours = Array.from({ length: 24 }, (_, hour) => `${String(hour).padStart(2, "0")}h`);
  const days = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
  const heatmap = days.map((_, dayIndex) =>
    hours.map((_, hour) => {
      const rush = hour >= 6 && hour <= 9 ? 1.28 : hour >= 17 && hour <= 20 ? 1.18 : hour <= 5 ? 0.82 : 1;
      return Number((average * rush * (0.9 + dayIndex * 0.025)).toFixed(1));
    })
  );

  const stationFactors = [0.72, 0.88, 1.02, 1.18, 1.34];
  const stationNames = ["Centro", "Zona Norte", "Zona Sul", "Zona Leste", "Zona Oeste"];

  return {
    city: filters.city,
    country: COUNTRY_NAMES[filters.country] || filters.country,
    parameter: filters.parameter,
    parameter_label: config.label,
    unit: config.unit,
    days: filters.days,
    who_limit: config.limit,
    source: "demo",
    source_note: "Versão pública demonstrativa. Os dados reais exigem o backend AirVision configurado.",
    updated_at: new Date().toISOString(),
    series,
    metrics: {
      average: Number(average.toFixed(1)),
      max_value: maxValue,
      max_date: dates[maxIndex],
      min_value: minValue,
      min_date: dates[minIndex],
      compliance_pct: Math.round(compliance),
      trend_per_year: Number(trend.toFixed(1)),
      previous_delta_pct: Number((((values.at(-1) - values[0]) / values[0]) * 100).toFixed(1)),
      quality_label: qualityLabel,
      quality_score: Math.max(0, Math.min(100, Math.round((average / (config.limit * 2.5)) * 100))),
    },
    stations: stationFactors.map((factor, index) => {
      const value = Number((average * factor).toFixed(1));
      const category = value <= config.limit ? "Bom" : value <= config.limit * 2.35 ? "Moderado" : "Ruim";
      const color = category === "Bom" ? "#15803D" : category === "Moderado" ? "#B45309" : "#DC2626";
      return { name: stationNames[index], value, category, color };
    }),
    critical_days: criticalDays,
    heatmap: { days, hours, z: heatmap },
  };
}
