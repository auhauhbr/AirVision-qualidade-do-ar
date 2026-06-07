const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export async function fetchMeasurements(filters) {
  const params = new URLSearchParams({
    country: filters.country,
    city: filters.city,
    parameter: filters.parameter,
    days: String(filters.days),
  });
  const response = await fetch(`${API_BASE}/api/measurements?${params.toString()}`);
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Não foi possível buscar os dados.");
  }
  return response.json();
}

export async function fetchOptions() {
  const response = await fetch(`${API_BASE}/api/options`);
  if (!response.ok) {
    throw new Error("Não foi possível buscar as opções de filtros.");
  }
  return response.json();
}

export function downloadSeriesCsv(data) {
  const header = ["date", "value", "sma7", "sma14", "anomaly"];
  const rows = data.series.map((row) =>
    header.map((key) => row[key] ?? "").join(",")
  );
  const blob = new Blob([[header.join(","), ...rows].join("\n")], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `airvision-${data.city}-${data.parameter}-${data.days}d.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}
