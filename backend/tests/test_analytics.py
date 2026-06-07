from backend.app.analytics import build_demo_daily, summarize


def test_summarize_demo_series_has_expected_shapes():
    df = build_demo_daily("Recife", "pm25", 30)
    payload = summarize(df, "pm25")

    assert len(payload["series"]) == 30
    assert payload["metrics"]["average"] > 0
    assert payload["metrics"]["max_value"] >= payload["metrics"]["min_value"]
    assert len(payload["critical_days"]) <= 6
