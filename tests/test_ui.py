from __future__ import annotations

import pandas as pd

from src.ui import app as app_ui
from src.ui import diagnostics as diagnostics_ui
from src.ui import overview as overview_ui
from src.ui import player_detail as player_detail_ui


class FakeContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeMetric:
    def __init__(self):
        self.metrics = []

    def metric(self, label, value):
        self.metrics.append((label, value))


class FakeStreamlit:
    def __init__(self, selectbox_values=None, slider_values=None, upload=None):
        self.selectbox_values = list(selectbox_values or [])
        self.slider_values = list(slider_values or [])
        self.upload = upload
        self.calls = []

    def set_page_config(self, **kwargs):
        self.calls.append(("set_page_config", kwargs))

    def title(self, value):
        self.calls.append(("title", value))

    def caption(self, value):
        self.calls.append(("caption", value))

    def file_uploader(self, *args, **kwargs):
        self.calls.append(("file_uploader", args, kwargs))
        return self.upload

    def info(self, value):
        self.calls.append(("info", value))

    def warning(self, value):
        self.calls.append(("warning", value))

    def spinner(self, value):
        self.calls.append(("spinner", value))
        return FakeContext()

    def columns(self, count):
        self.calls.append(("columns", count))
        return [FakeMetric() for _ in range(count)]

    def tabs(self, labels):
        self.calls.append(("tabs", labels))
        return [FakeContext() for _ in labels]

    def subheader(self, value):
        self.calls.append(("subheader", value))

    def selectbox(self, label, options, index=0):
        self.calls.append(("selectbox", label, options, index))
        if self.selectbox_values:
            return self.selectbox_values.pop(0)
        return options[index]

    def slider(self, label, min_value, max_value, value):
        self.calls.append(("slider", label, min_value, max_value, value))
        if self.slider_values:
            return self.slider_values.pop(0)
        return value

    def dataframe(self, value, **kwargs):
        self.calls.append(("dataframe", type(value).__name__, kwargs))

    def download_button(self, *args, **kwargs):
        self.calls.append(("download_button", args, kwargs))

    def vega_lite_chart(self, *args, **kwargs):
        self.calls.append(("vega_lite_chart", args, kwargs))

    def bar_chart(self, value):
        self.calls.append(("bar_chart", value))

    def markdown(self, value):
        self.calls.append(("markdown", value))


def sample_results():
    return pd.DataFrame(
        {
            "player": ["A", "A", "B"],
            "player_role_id": ["0::ST", "0::AM_W", "1::ST"],
            "club": ["X", "X", "Y"],
            "age": [22, 22, 25],
            "minutes": [900, 900, 1200],
            "performance_score": [70.0, 65.0, 80.0],
            "cost_score": [30.0, 40.0, 60.0],
            "value_gap_score": [85.0, 70.0, 55.0],
            "uncertainty_score": [40.0, 45.0, 20.0],
            "broad_role": ["ST", "AM_W", "ST"],
            "performance_raw": [0.2, 0.1, 0.5],
            "cost_raw": [-0.4, -0.2, 0.3],
            "value_gap_raw": [1.0, 0.5, -0.5],
            "uncertainty_raw": [-0.1, 0.2, -0.7],
            "bootstrap_sd": [0.1, 0.2, 0.05],
            "shrinkage_intensity": [0.2, 0.25, 0.1],
            "exposure_uncertainty": [0.3, 0.3, 0.2],
            "Transfer Value": [1_000_000.0, 1_000_000.0, 2_000_000.0],
            "Wage": [10_000.0, 10_000.0, 20_000.0],
            "threat__score": [80.0, 70.0, 90.0],
            "threat__raw": [0.4, 0.2, 0.8],
            "creation__score": [60.0, 75.0, 50.0],
            "creation__raw": [0.1, 0.3, -0.1],
        }
    )


def sample_traces():
    raw = pd.DataFrame(
        {
            "player_role_id": ["0::ST", "0::AM_W", "1::ST"],
            "Shot/90": [2.0, 1.5, 3.0],
            "KP/90": [0.5, 1.0, 0.7],
        }
    )
    matrix = pd.DataFrame({"Shot/90": [0.1, 0.0, 0.2], "KP/90": [0.0, 0.2, 0.1]})
    return {
        "ST": {"raw_primitives": raw.iloc[[0, 2]].reset_index(drop=True), "shrunk": matrix.iloc[[0, 2]].reset_index(drop=True), "standardized": matrix.iloc[[0, 2]].reset_index(drop=True), "adjusted": matrix.iloc[[0, 2]].reset_index(drop=True)},
        "AM_W": {"raw_primitives": raw.iloc[[1]].reset_index(drop=True), "shrunk": matrix.iloc[[1]].reset_index(drop=True), "standardized": matrix.iloc[[1]].reset_index(drop=True), "adjusted": matrix.iloc[[1]].reset_index(drop=True)},
    }


def sample_diagnostics():
    return {
        "load_meta": {"missingness": pd.Series({"A": 0.0}), "row_count": 3, "warnings": ["warn"]},
        "role_sizes": pd.Series({"AM_W": 1, "ST": 2}),
        "role_artifacts": {
            "ST": {"family": {"threat": {"kept": ["Shot/90", "KP/90"], "explained_variance": 0.6}}, "performance": {"explained_variance": 0.7}},
            "AM_W": {"family": {"creation": {"kept": ["KP/90"], "explained_variance": None}}, "performance": {"explained_variance": None}},
        },
        "role_warnings": {"ST": ["low sample"], "AM_W": []},
        "dropped_columns": {"ST": {"threat": ["xG/90"]}, "AM_W": {"creation": []}},
    }


def test_render_overview_handles_empty(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(overview_ui, "st", fake)
    overview_ui.render_overview(pd.DataFrame())
    assert ("info", "No eligible player-role rows were produced from the upload.") in fake.calls


def test_render_overview_full(monkeypatch):
    fake = FakeStreamlit(selectbox_values=["All", "All"], slider_values=[(15, 45), (0, 1200)])
    monkeypatch.setattr(overview_ui, "st", fake)
    overview_ui.render_overview(sample_results())
    assert any(call[0] == "download_button" for call in fake.calls)
    assert any(call[0] == "vega_lite_chart" for call in fake.calls)


def test_render_overview_handles_zero_minutes(monkeypatch):
    fake = FakeStreamlit(selectbox_values=["All", "All"], slider_values=[(15, 45)])
    monkeypatch.setattr(overview_ui, "st", fake)
    results = sample_results().copy()
    results["minutes"] = 0
    overview_ui.render_overview(results)
    assert any(call[0] == "info" and "Minutes filter is unavailable" in call[1] for call in fake.calls)


def test_render_player_detail_handles_empty(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(player_detail_ui, "st", fake)
    player_detail_ui.render_player_detail(pd.DataFrame(), {}, {})
    assert ("info", "No scored players are available.") in fake.calls


def test_render_player_detail_full(monkeypatch):
    fake = FakeStreamlit(selectbox_values=["A", "ST"])
    monkeypatch.setattr(player_detail_ui, "st", fake)
    player_detail_ui.render_player_detail(sample_results(), sample_traces(), sample_diagnostics())
    assert any(call[0] == "bar_chart" for call in fake.calls)
    assert any(call[0] == "warning" and call[1] == "low sample" for call in fake.calls)


def test_render_diagnostics(monkeypatch):
    fake = FakeStreamlit(selectbox_values=["ST"])
    monkeypatch.setattr(diagnostics_ui, "st", fake)
    payload = {"results": sample_results(), "traces": sample_traces(), "diagnostics": sample_diagnostics()}
    diagnostics_ui.render_diagnostics(payload)
    assert any(call[0] == "bar_chart" for call in fake.calls)
    assert any(call[0] == "dataframe" for call in fake.calls)


def test_app_main_without_upload(monkeypatch):
    fake = FakeStreamlit(upload=None)
    monkeypatch.setattr(app_ui, "st", fake)
    app_ui.main()
    assert ("info", "Upload a semicolon-delimited FM export to build the cohort dashboard.") in fake.calls


def test_app_main_with_upload(monkeypatch):
    fake = FakeStreamlit(upload=object())
    monkeypatch.setattr(app_ui, "st", fake)
    payload = {"results": sample_results(), "traces": sample_traces(), "diagnostics": sample_diagnostics(), "load_meta": {"warnings": ["warn"], "row_count": 3}}
    monkeypatch.setattr(app_ui, "run_pipeline", lambda upload: payload)
    called = {"overview": False, "player": False, "diag": False}
    monkeypatch.setattr(app_ui, "render_overview", lambda results: called.__setitem__("overview", True))
    monkeypatch.setattr(app_ui, "render_player_detail", lambda results, traces, diagnostics: called.__setitem__("player", True))
    monkeypatch.setattr(app_ui, "render_diagnostics", lambda payload_arg: called.__setitem__("diag", True))
    app_ui.main()
    assert all(called.values())
