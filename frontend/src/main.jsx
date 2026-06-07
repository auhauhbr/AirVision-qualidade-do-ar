import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import Plot from "react-plotly.js";
import { downloadSeriesCsv, fetchMeasurements, fetchOptions } from "./services/api";
import "./styles.css";

const FALLBACK_COUNTRIES = [
  { code: "BR", label: "Brasil", cities: ["Rio de Janeiro", "São Paulo", "Manaus", "Fortaleza", "Recife"] },
  { code: "AR", label: "Argentina", cities: ["Buenos Aires", "Córdoba", "Mendoza"] },
  { code: "PT", label: "Portugal", cities: ["Lisboa", "Porto", "Braga", "Coimbra"] },
  { code: "US", label: "Estados Unidos", cities: ["Los Angeles", "New York", "Chicago", "Houston", "Seattle"] },
];

const PARAMETERS = [
  { value: "pm25", label: "PM2.5 - Partículas finas" },
  { value: "pm10", label: "PM10 - Partículas inaláveis" },
  { value: "no2", label: "NO₂ - Dióxido de nitrogênio" },
  { value: "o3", label: "O₃ - Ozônio" },
  { value: "co", label: "CO - Monóxido de carbono" },
  { value: "so2", label: "SO₂ - Dióxido de enxofre" },
];

const PERIODS = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
  { label: "1a", days: 365 },
];

function formatDate(value) {
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short" }).format(new Date(`${value}T00:00:00`));
}

function formatFullDate(value) {
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`));
}

function Header({ source }) {
  return (
    <header className="header">
      <div className="header-left">
        <div className="logo">
          <div className="logo-mark" aria-hidden="true">
            <svg viewBox="0 0 16 16"><path d="M8 1C4.13 1 1 4.13 1 8s3.13 7 7 7 7-3.13 7-7-3.13-7-7-7zm0 2a5 5 0 110 10A5 5 0 018 3zm0 2a3 3 0 100 6 3 3 0 000-6z" /></svg>
          </div>
          <span className="logo-name">AirVision</span>
        </div>
        <div className="header-divider" />
        <span className="header-subtitle">Qualidade do Ar - Análise Histórica</span>
      </div>
      <div className="header-right">
        <span className="badge badge-live">AO VIVO</span>
        <span className="badge badge-muted">{source === "openaq" || source === "cache" ? "OpenAQ v3" : "Demo local"}</span>
      </div>
    </header>
  );
}

function Sidebar({ filters, setFilters, onRefresh, data, loading, countries }) {
  const currentCountry = countries.find((item) => item.code === filters.country) || countries[0];

  function updateCountry(country) {
    const target = countries.find((item) => item.code === country) || countries[0];
    setFilters((prev) => ({ ...prev, country, city: target.cities[0] }));
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <div className="sidebar-label">Localização</div>
        <div className="control-group">
          <label className="control-label" htmlFor="country">País</label>
          <select id="country" value={filters.country} onChange={(event) => updateCountry(event.target.value)}>
            {countries.map((country) => <option key={country.code} value={country.code}>{country.label}</option>)}
          </select>
        </div>
        <div className="control-group">
          <label className="control-label" htmlFor="city">Cidade</label>
          <select id="city" value={filters.city} onChange={(event) => setFilters((prev) => ({ ...prev, city: event.target.value }))}>
            {currentCountry.cities.map((city) => <option key={city}>{city}</option>)}
          </select>
        </div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">Poluente</div>
        <div className="control-group">
          <label className="control-label" htmlFor="pollutant-select">Parâmetro</label>
          <select id="pollutant-select" value={filters.parameter} onChange={(event) => setFilters((prev) => ({ ...prev, parameter: event.target.value }))}>
            {PARAMETERS.map((parameter) => <option key={parameter.value} value={parameter.value}>{parameter.label}</option>)}
          </select>
        </div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">Período</div>
        <div className="period-tabs">
          {PERIODS.map((period) => (
            <button
              key={period.days}
              className={`period-tab ${filters.days === period.days ? "active" : ""}`}
              onClick={() => setFilters((prev) => ({ ...prev, days: period.days }))}
              type="button"
            >
              {period.label}
            </button>
          ))}
        </div>
        <div className="spacer-sm" />
        <button className="apply-btn" onClick={onRefresh} disabled={loading} type="button">
          {loading ? "Atualizando..." : "Atualizar dados"}
        </button>
      </div>

      <div className="sidebar-divider" />
      <div className="sidebar-section">
        <div className="sidebar-label">Estações ativas</div>
        <div className="station-list">
          {(data?.stations || []).map((station) => (
            <div className="station-item" key={station.name} title={station.category}>
              <div className="station-dot" style={{ background: station.color }} />
              <span className="station-name">{station.name}</span>
              <span className="station-val">{station.value.toFixed(1)}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}

function MetricCard({ label, value, unit, delta, tone = "", highlight = false }) {
  return (
    <div className={`metric-card ${highlight ? "highlight" : ""}`}>
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${tone}`}>{value}</div>
      <div className="metric-unit">{unit}</div>
      <div className={`metric-delta ${tone === "green" ? "delta-down" : tone === "red" ? "delta-up" : ""}`}>{delta}</div>
    </div>
  );
}

function Metrics({ data }) {
  const metric = data.metrics;
  const trendTone = metric.trend_per_year <= 0 ? "green" : "red";
  const deltaText = metric.previous_delta_pct == null
    ? "Sem base anterior suficiente"
    : `${metric.previous_delta_pct > 0 ? "↑" : "↓"} ${Math.abs(metric.previous_delta_pct)}% vs. início do período`;
  return (
    <div className="metrics-row">
      <MetricCard
        highlight
        label="Média do período"
        value={metric.average.toFixed(1)}
        unit={`${data.unit} · ${data.parameter_label}`}
        delta={deltaText}
        tone={metric.previous_delta_pct > 0 ? "red" : "green"}
      />
      <MetricCard
        label="Pior dia registrado"
        value={formatDate(metric.max_date)}
        unit={`${metric.max_value.toFixed(1)} ${data.unit} · anomalia detectada`}
        delta={`↑ ${Math.round(((metric.max_value - metric.average) / metric.average) * 100)}% acima da média`}
        tone="red"
      />
      <MetricCard
        label="Conformidade OMS"
        value={`${metric.compliance_pct.toFixed(0)}%`}
        unit={`dos dias abaixo de ${data.who_limit} ${data.unit}`}
        delta={`${metric.quality_label} · IQA ${metric.quality_score}`}
      />
      <MetricCard
        label="Tendência anual"
        value={`${metric.trend_per_year > 0 ? "+" : ""}${metric.trend_per_year.toFixed(1)}`}
        unit={`${data.unit} por ano · regressão linear`}
        delta={metric.trend_per_year <= 0 ? "↓ Melhora consistente" : "↑ Atenção à piora"}
        tone={trendTone}
      />
    </div>
  );
}

function BootstrapIcon({ name }) {
  const paths = {
    gauge: (
      <>
        <path d="M8 4a.5.5 0 0 1 .5.5V6a.5.5 0 0 1-1 0V4.5A.5.5 0 0 1 8 4z" />
        <path d="M3.732 5.732a.5.5 0 0 1 .707 0l.915.914a.5.5 0 1 1-.708.708l-.914-.915a.5.5 0 0 1 0-.707z" />
        <path d="M2 10a.5.5 0 0 1 .5-.5H4a.5.5 0 0 1 0 1H2.5A.5.5 0 0 1 2 10z" />
        <path d="M14 10a.5.5 0 0 1-.5.5H12a.5.5 0 0 1 0-1h1.5a.5.5 0 0 1 .5.5z" />
        <path d="M10.646 7.354a.5.5 0 0 1 0-.708l.915-.914a.5.5 0 0 1 .707.707l-.914.915a.5.5 0 0 1-.708 0z" />
        <path d="M8.5 10.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z" />
        <path d="M4.5 13a.5.5 0 0 1-.39-.188A6.5 6.5 0 1 1 13 10.5a6.47 6.47 0 0 1-1.11 3.312.5.5 0 0 1-.78-.624A5.5 5.5 0 1 0 3.5 10.5c0 .94.234 1.823.64 2.593A.5.5 0 0 1 3.25 13H4.5z" />
      </>
    ),
    calendar: (
      <>
        <path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z" />
        <path d="M4 7h2v2H4V7zm3 0h2v2H7V7zm3 0h2v2h-2V7zM4 10h2v2H4v-2zm3 0h2v2H7v-2zm3 0h2v2h-2v-2z" />
      </>
    ),
    broadcast: (
      <>
        <path d="M3.05 3.05a7 7 0 0 0 0 9.9.5.5 0 0 1-.707.707 8 8 0 0 1 0-11.314.5.5 0 0 1 .707.707zm2.122 2.122a4 4 0 0 0 0 5.656.5.5 0 1 1-.708.708 5 5 0 0 1 0-7.072.5.5 0 0 1 .708.708zm5.656-.708a.5.5 0 0 1 .708 0 5 5 0 0 1 0 7.072.5.5 0 1 1-.708-.708 4 4 0 0 0 0-5.656.5.5 0 0 1 0-.708zm2.122-2.121a.5.5 0 0 1 .707 0 8 8 0 0 1 0 11.314.5.5 0 0 1-.707-.707 7 7 0 0 0 0-9.9.5.5 0 0 1 0-.707z" />
        <path d="M8 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" />
      </>
    ),
  };

  return (
    <svg className="status-bootstrap-icon" viewBox="0 0 16 16" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}

function MainChart({ data, overlay, setOverlay }) {
  const traces = useMemo(() => {
    const x = data.series.map((point) => point.date);
    const y = data.series.map((point) => point.value);
    const base = [
      {
        x,
        y: x.map(() => data.who_limit),
        mode: "lines",
        name: "Limite OMS",
        line: { color: "#DC2626", width: 1.5, dash: "dot" },
        hoverinfo: "skip",
      },
      {
        x,
        y,
        mode: "lines",
        name: `${data.parameter_label} diário`,
        fill: "tozeroy",
        fillcolor: "rgba(28,110,242,0.07)",
        line: { color: "#1C6EF2", width: 2 },
        hovertemplate: `<b>%{y:.1f} ${data.unit}</b><br>%{x}<extra></extra>`,
      },
    ];
    if (overlay === "sma7" || overlay === "sma14") {
      base.push({
        x,
        y: data.series.map((point) => point.sma7),
        mode: "lines",
        name: "SMA 7d",
        line: { color: "#B45309", width: 2 },
        hovertemplate: "SMA 7d: <b>%{y:.1f}</b><extra></extra>",
      });
    }
    if (overlay === "sma14") {
      base.push({
        x,
        y: data.series.map((point) => point.sma14),
        mode: "lines",
        name: "SMA 14d",
        line: { color: "#15803D", width: 2 },
        hovertemplate: "SMA 14d: <b>%{y:.1f}</b><extra></extra>",
      });
    }
    if (overlay === "anomaly") {
      const anomalies = data.series.filter((point) => point.anomaly);
      base.push({
        x: anomalies.map((point) => point.date),
        y: anomalies.map((point) => point.value),
        mode: "markers",
        name: "Anomalia",
        marker: { color: "#DC2626", size: 10, symbol: "circle", line: { color: "white", width: 2 } },
        hovertemplate: `<b>%{y:.1f} ${data.unit}</b><br>%{x}<extra></extra>`,
      });
    }
    return base;
  }, [data, overlay]);

  return (
    <div className="chart-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">{data.parameter_label} - Série temporal · {data.city}, {data.country}</div>
          <div className="panel-sub">Últimos {data.days} dias · média diária por estação</div>
        </div>
        <div className="panel-actions">
          {[
            ["none", "Bruto"],
            ["sma7", "SMA 7d"],
            ["sma14", "SMA 14d"],
            ["anomaly", "Anomalias"],
          ].map(([value, label]) => (
            <button key={value} className={`pill-btn ${overlay === value ? "active" : ""}`} onClick={() => setOverlay(value)} type="button">
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="chart-body">
        <Plot
          data={traces}
          layout={{
            margin: { t: 16, r: 16, b: 36, l: 44 },
            height: 260,
            paper_bgcolor: "white",
            plot_bgcolor: "white",
            xaxis: { showgrid: false, tickfont: { family: "DM Mono", size: 11, color: "#A8A8A4" }, linecolor: "#E4E4E0", linewidth: 1, ticks: "" },
            yaxis: { showgrid: true, gridcolor: "#F0F0EE", gridwidth: 1, tickfont: { family: "DM Mono", size: 11, color: "#A8A8A4" }, ticksuffix: " µ", zeroline: false, ticks: "" },
            legend: { orientation: "h", x: 0, y: 1.08, font: { family: "DM Sans", size: 11, color: "#6B6B67" }, bgcolor: "rgba(0,0,0,0)" },
            hovermode: "x unified",
            hoverlabel: { bgcolor: "white", bordercolor: "#E4E4E0", font: { family: "DM Sans", size: 12 } },
          }}
          config={{ responsive: true, displayModeBar: false }}
          className="plotly-chart"
          useResizeHandler
        />
      </div>
    </div>
  );
}

function StatusRow({ data }) {
  const metric = data.metrics;
  const sourceText = data.source === "demo" ? "modo demonstração" : data.source === "cache" ? "cache local" : "OpenAQ";
  return (
    <div className="status-row">
      <div className="status-card">
        <div className="status-icon status-good"><BootstrapIcon name="gauge" /></div>
        <div className="status-info">
          <div className="status-title">Hoje · {metric.quality_label}</div>
          <div className="status-desc">IQA {metric.quality_score} · {data.parameter_label}: {metric.average.toFixed(1)} {data.unit}</div>
          <div className="quality-bar">
            <div className="q-seg" style={{ background: "#15803D", flex: Math.max(1, 100 - metric.quality_score) }} />
            <div className="q-seg" style={{ background: "#B45309", flex: 28, opacity: 0.3 }} />
            <div className="q-seg" style={{ background: "#DC2626", flex: metric.quality_score, opacity: 0.2 }} />
          </div>
        </div>
      </div>
      <div className="status-card">
        <div className="status-icon status-warn"><BootstrapIcon name="calendar" /></div>
        <div className="status-info">
          <div className="status-title">Sazonalidade estimada</div>
          <div className="status-desc">Padrão horário derivado da série recente</div>
          <div className="quality-bar quality-months">
            {Array.from({ length: 12 }, (_, index) => <div key={index} className="q-seg" />)}
          </div>
        </div>
      </div>
      <div className="status-card">
        <div className="status-icon status-api"><BootstrapIcon name="broadcast" /></div>
        <div className="status-info">
          <div className="status-title">{data.stations.length} estações · {sourceText}</div>
          <div className="status-desc">Última sync: {new Date(data.updated_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })} · {data.series.length} dias</div>
          <div className="quality-bar">
            <div className="q-seg" style={{ background: "#15803D", flex: 4 }} />
            <div className="q-seg" style={{ background: data.source === "demo" ? "#B45309" : "#1C6EF2", flex: 1 }} />
          </div>
        </div>
      </div>
    </div>
  );
}

function HeatmapChart({ data }) {
  return (
    <div className="chart-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Heatmap · Hora × Dia da semana</div>
          <div className="panel-sub">{data.parameter_label} médio - últimos {Math.min(data.days, 90)} dias</div>
        </div>
      </div>
      <Plot
        data={[{
          z: data.heatmap.z,
          x: data.heatmap.hours,
          y: data.heatmap.days,
          type: "heatmap",
          colorscale: [[0, "#EBF2FE"], [0.35, "#93C5FD"], [0.7, "#B45309"], [1, "#DC2626"]],
          showscale: true,
          colorbar: { len: 0.8, thickness: 10, tickfont: { family: "DM Mono", size: 10, color: "#A8A8A4" }, ticksuffix: "µ", outlinewidth: 0 },
          hovertemplate: `<b>%{y} · %{x}</b><br>${data.parameter_label}: %{z:.1f} ${data.unit}<extra></extra>`,
        }]}
        layout={{
          margin: { t: 12, r: 60, b: 36, l: 40 },
          height: 220,
          paper_bgcolor: "white",
          plot_bgcolor: "white",
          xaxis: { tickfont: { family: "DM Mono", size: 10, color: "#A8A8A4" }, tickangle: -45, showgrid: false },
          yaxis: { tickfont: { family: "DM Mono", size: 11, color: "#A8A8A4" }, showgrid: false },
          hoverlabel: { bgcolor: "white", bordercolor: "#E4E4E0", font: { family: "DM Sans", size: 12 } },
        }}
        config={{ responsive: true, displayModeBar: false }}
        className="plotly-chart"
        useResizeHandler
      />
    </div>
  );
}

function CriticalTable({ data }) {
  return (
    <div className="table-panel">
      <div className="table-header">
        <div className="panel-title">Dias críticos detectados</div>
        <button className="export-btn" onClick={() => downloadSeriesCsv(data)} type="button">Exportar CSV</button>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Data</th>
            <th>{data.parameter_label}</th>
            <th>Δ Média</th>
            <th>IQA</th>
          </tr>
        </thead>
        <tbody>
          {data.critical_days.map((day) => (
            <tr key={day.date}>
              <td>{formatFullDate(day.date)}</td>
              <td className="mono">{day.value.toFixed(1)}</td>
              <td className={day.delta_pct >= 0 ? "danger" : "success"}>{day.delta_pct > 0 ? "+" : ""}{day.delta_pct.toFixed(0)}%</td>
              <td><span className={`aqi-pill ${day.category === "Bom" ? "aqi-good" : day.category === "Moderado" ? "aqi-moderate" : "aqi-bad"}`}>{day.category}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  const [countries, setCountries] = useState(FALLBACK_COUNTRIES);
  const [filters, setFilters] = useState({ country: "BR", city: "Rio de Janeiro", parameter: "pm25", days: 30 });
  const [requestId, setRequestId] = useState(0);
  const [overlay, setOverlay] = useState("none");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchOptions()
      .then((payload) => {
        if (!active) {
          return;
        }
        const mappedCountries = payload.countries.map((country) => ({
          code: country.code,
          label: country.name,
          cities: Object.keys(payload.cities[country.code] || {}),
        })).filter((country) => country.cities.length > 0);
        if (mappedCountries.length) {
          setCountries(mappedCountries);
        }
      })
      .catch(() => {
        setCountries(FALLBACK_COUNTRIES);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    fetchMeasurements(filters)
      .then((payload) => {
        if (active) {
          setData(payload);
        }
      })
      .catch((exc) => {
        if (active) {
          setError(exc.message);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [filters.country, filters.city, filters.parameter, filters.days, requestId]);

  return (
    <>
      <Header source={data?.source} />
      <div className="layout">
        <Sidebar filters={filters} setFilters={setFilters} onRefresh={() => setRequestId((value) => value + 1)} data={data} loading={loading} countries={countries} />
        <main className="main">
          {error && <div className="notice error">{error}</div>}
          {data?.source_note && <div className="notice">{data.source_note}</div>}
          {data ? (
            <>
              <Metrics data={data} />
              <MainChart data={data} overlay={overlay} setOverlay={setOverlay} />
              <StatusRow data={data} />
              <div className="bottom-grid">
                <HeatmapChart data={data} />
                <CriticalTable data={data} />
              </div>
            </>
          ) : (
            <div className="chart-panel loading-panel">Carregando AirVision...</div>
          )}
        </main>
      </div>
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
