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
        self.tables = []
        self.text = []

    def metric(self, label, value):
        self.metrics.append((label, value))

    def markdown(self, value):
        self.text.append(value)

    def dataframe(self, value, **kwargs):
        self.tables.append((value, kwargs))


class FakeProgress:
    def __init__(self, calls):
        self.calls = calls

    def progress(self, value):
        self.calls.append(("progress_update", value))

    def empty(self):
        self.calls.append(("progress_empty",))


class FakeEmpty:
    def __init__(self, calls):
        self.calls = calls

    def caption(self, value):
        self.calls.append(("caption_update", value))

    def empty(self):
        self.calls.append(("empty_clear",))


class FakeStreamlit:
    def __init__(self, selectbox_values=None, slider_values=None, upload=None, checkbox_values=None, multiselect_values=None, toggle_values=None):
        self.selectbox_values = list(selectbox_values or [])
        self.slider_values = list(slider_values or [])
        self.checkbox_values = list(checkbox_values or [])
        self.multiselect_values = list(multiselect_values or [])
        self.toggle_values = list(toggle_values or [])
        self.upload = upload
        self.calls = []
        self.session_state = {}

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

    def progress(self, value):
        self.calls.append(("progress", value))
        return FakeProgress(self.calls)

    def empty(self):
        self.calls.append(("empty",))
        return FakeEmpty(self.calls)

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

    def selectbox(self, label, options, index=0, **kwargs):
        self.calls.append(("selectbox", label, options, index, kwargs))
        if self.selectbox_values:
            return self.selectbox_values.pop(0)
        return options[index]

    def multiselect(self, label, options, default=None, max_selections=None):
        self.calls.append(("multiselect", label, options, default, max_selections))
        if self.multiselect_values:
            return self.multiselect_values.pop(0)
        return default or []

    def slider(self, label, min_value, max_value, value):
        self.calls.append(("slider", label, min_value, max_value, value))
        if self.slider_values:
            return self.slider_values.pop(0)
        return value

    def checkbox(self, label, value=False):
        self.calls.append(("checkbox", label, value))
        if self.checkbox_values:
            return self.checkbox_values.pop(0)
        return value

    def toggle(self, label, value=False, key=None):
        self.calls.append(("toggle", label, value, key))
        if self.toggle_values:
            return self.toggle_values.pop(0)
        return value

    def dataframe(self, value, **kwargs):
        self.calls.append(("dataframe", type(value).__name__, kwargs))

    def download_button(self, *args, **kwargs):
        self.calls.append(("download_button", args, kwargs))

    def vega_lite_chart(self, *args, **kwargs):
        self.calls.append(("vega_lite_chart", args, kwargs))

    def bar_chart(self, value):
        self.calls.append(("bar_chart", value))

    def markdown(self, value, **kwargs):
        self.calls.append(("markdown", value, kwargs))

    def button(self, label):
        self.calls.append(("button", label))
        return False

    def rerun(self):
        self.calls.append(("rerun",))

    def expander(self, label):
        self.calls.append(("expander", label))
        return FakeContext()


def sample_results():
    return pd.DataFrame(
        {
            "player": ["A", "A", "B"],
            "player_role_id": ["0::ST", "0::AM_W", "1::ST"],
            "cohort_key": ["Division A::ST", "Division A::AM_W", "Division B::ST"],
            "division": ["Division A", "Division A", "Division B"],
            "club": ["X", "X", "Y"],
            "position": ["ST", "AM (R), ST", "ST"],
            "age": [22, 22, 25],
            "minutes": [900, 900, 1200],
            "goals": [12, 7, 18],
            "assists": [4, 9, 3],
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
            "finisher__score": [80.0, 70.0, 90.0],
            "finisher__raw": [0.4, 0.2, 0.8],
            "creation__score": [60.0, 75.0, 50.0],
            "creation__raw": [0.1, 0.3, -0.1],
        }
    )


def sample_traces():
    raw = pd.DataFrame(
        {
            "player_role_id": ["0::ST", "0::AM_W", "1::ST"],
            "Division__raw": ["Division A", "Division A", "Division B"],
            "broad_role": ["ST", "AM_W", "ST"],
            "Shot/90": [2.0, 1.5, 3.0],
            "KP/90": [0.5, 1.0, 0.7],
        }
    )
    matrix = pd.DataFrame({"Shot/90": [0.1, 0.0, 0.2], "KP/90": [0.0, 0.2, 0.1]})
    return {
        "Division A::ST": {
            "raw_primitives": raw.iloc[[0]].reset_index(drop=True),
            "shrunk": matrix.iloc[[0]].reset_index(drop=True),
            "standardized": matrix.iloc[[0]].reset_index(drop=True),
            "adjusted": matrix.iloc[[0]].reset_index(drop=True),
            "metric_percentiles": pd.DataFrame({"Shot/90": [80.0], "KP/90": [60.0]}),
        },
        "Division A::AM_W": {
            "raw_primitives": raw.iloc[[1]].reset_index(drop=True),
            "shrunk": matrix.iloc[[1]].reset_index(drop=True),
            "standardized": matrix.iloc[[1]].reset_index(drop=True),
            "adjusted": matrix.iloc[[1]].reset_index(drop=True),
            "metric_percentiles": pd.DataFrame({"Shot/90": [70.0], "KP/90": [75.0]}),
        },
        "Division B::ST": {
            "raw_primitives": raw.iloc[[2]].reset_index(drop=True),
            "shrunk": matrix.iloc[[2]].reset_index(drop=True),
            "standardized": matrix.iloc[[2]].reset_index(drop=True),
            "adjusted": matrix.iloc[[2]].reset_index(drop=True),
            "metric_percentiles": pd.DataFrame({"Shot/90": [90.0], "KP/90": [50.0]}),
        },
    }


def sample_diagnostics():
    return {
        "load_meta": {"missingness": pd.Series({"A": 0.0}), "row_count": 3, "warnings": ["warn"]},
        "role_sizes": pd.Series(
            [1, 1, 1],
            index=pd.MultiIndex.from_tuples(
                [("Division A", "AM_W"), ("Division A", "ST"), ("Division B", "ST")],
                names=["Division__raw", "broad_role"],
            ),
        ),
        "role_artifacts": {
            "Division A::ST": {"family": {"finisher": {"kept": ["Shot/90", "KP/90"], "explained_variance": 0.6}}, "performance": {"explained_variance": 0.7}},
            "Division A::AM_W": {"family": {"creator": {"kept": ["KP/90"], "explained_variance": None}}, "performance": {"explained_variance": None}},
            "Division B::ST": {"family": {"finisher": {"kept": ["Shot/90"], "explained_variance": None}}, "performance": {"explained_variance": None}},
        },
        "role_warnings": {"Division A::ST": ["low sample"], "Division A::AM_W": [], "Division B::ST": []},
        "dropped_columns": {"Division A::ST": {"finisher": ["xG/90"]}, "Division A::AM_W": {"creator": []}, "Division B::ST": {"finisher": []}},
    }


def test_render_overview_handles_empty(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(overview_ui, "st", fake)
    overview_ui.render_overview(pd.DataFrame(), {})
    assert ("info", "No eligible player-role rows were produced from the upload.") in fake.calls


def test_render_overview_full(monkeypatch):
    fake = FakeStreamlit(selectbox_values=["All", "All", "AM_W"], slider_values=[(15, 45), (0, 1200), 15], toggle_values=[False, False])
    monkeypatch.setattr(overview_ui, "st", fake)
    overview_ui.render_overview(sample_results(), sample_traces())
    assert any(call[0] == "download_button" for call in fake.calls)
    assert any(call[0] == "vega_lite_chart" for call in fake.calls)
    assert any(call[0] == "dataframe" and "column_config" in call[2] for call in fake.calls)


def test_render_overview_handles_zero_minutes(monkeypatch):
    fake = FakeStreamlit(selectbox_values=["All", "All", "AM_W"], slider_values=[(15, 45), 15], toggle_values=[False, False])
    monkeypatch.setattr(overview_ui, "st", fake)
    results = sample_results().copy()
    results["minutes"] = 0
    overview_ui.render_overview(results, sample_traces())
    assert any(call[0] == "info" and "Minutes filter is unavailable" in call[1] for call in fake.calls)


def test_render_overview_shows_league_rankings(monkeypatch):
    fake = FakeStreamlit(selectbox_values=["All", "All", "ST"], multiselect_values=[["Division A"]], slider_values=[(15, 45), (0, 1200), 15], toggle_values=[False])
    monkeypatch.setattr(overview_ui, "st", fake)
    overview_ui.render_overview(sample_results(), sample_traces())
    assert not any(call[0] == "selectbox" and call[1] == "Trait To Rank" for call in fake.calls)


def test_render_overview_stats_view(monkeypatch):
    fake = FakeStreamlit(selectbox_values=["All", "All", "ST"], multiselect_values=[["Division A"]], slider_values=[(15, 45), (0, 1200), 15], toggle_values=[True])
    monkeypatch.setattr(overview_ui, "st", fake)
    overview_ui.render_overview(sample_results(), sample_traces())
    assert any(call[0] == "toggle" and "Stats View For Division A" in call[1] for call in fake.calls)
    assert any(call[0] == "dataframe" for call in fake.calls)


def test_render_player_detail_handles_empty(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(player_detail_ui, "st", fake)
    player_detail_ui.render_player_detail(pd.DataFrame(), {}, {})
    assert ("info", "No scored players are available.") in fake.calls


def test_render_player_detail_full(monkeypatch):
    fake = FakeStreamlit(selectbox_values=["A", "Division A | ST"], multiselect_values=[["A", "B"]])
    monkeypatch.setattr(player_detail_ui, "st", fake)
    player_detail_ui.render_player_detail(sample_results(), sample_traces(), sample_diagnostics())
    assert any(call[0] == "bar_chart" for call in fake.calls)
    assert sum(1 for call in fake.calls if call[0] == "vega_lite_chart") >= 1
    assert any(call[0] == "multiselect" for call in fake.calls)
    assert any(call[0] == "warning" and call[1] == "low sample" for call in fake.calls)


def test_render_diagnostics(monkeypatch):
    fake = FakeStreamlit(selectbox_values=["Division A::ST"])
    monkeypatch.setattr(diagnostics_ui, "st", fake)
    payload = {"results": sample_results(), "traces": sample_traces(), "diagnostics": sample_diagnostics()}
    diagnostics_ui.render_diagnostics(payload)
    assert any(call[0] == "dataframe" for call in fake.calls)


def test_app_main_without_upload(monkeypatch):
    fake = FakeStreamlit(upload=None)
    monkeypatch.setattr(app_ui, "st", fake)
    app_ui.main()
    assert ("info", "Upload a semicolon-delimited FM export to build the cohort dashboard.") in fake.calls


def test_app_main_with_upload(monkeypatch):
    fake = FakeStreamlit(upload=object(), checkbox_values=[False])
    monkeypatch.setattr(app_ui, "st", fake)
    payload = {
        "results": sample_results(),
        "traces": sample_traces(),
        "diagnostics": sample_diagnostics(),
        "load_meta": {"warnings": ["warn"], "row_count": 3, "file_hash": "abc"},
        "uncertainty_state": "complete",
    }
    monkeypatch.setattr(app_ui, "run_pipeline", lambda upload, progress_callback=None: payload)
    monkeypatch.setattr(app_ui, "_resolve_uncertainty_future", lambda payload: (payload, None))
    called = {"overview": False, "player": False, "diag": False}
    monkeypatch.setattr(app_ui, "render_overview", lambda results, traces: called.__setitem__("overview", True))
    monkeypatch.setattr(app_ui, "render_player_detail", lambda results, traces, diagnostics: called.__setitem__("player", True))
    monkeypatch.setattr(app_ui, "render_diagnostics", lambda payload_arg: called.__setitem__("diag", True))
    app_ui.main()
    assert called["overview"] is True
    assert called["player"] is True
    assert called["diag"] is False


def test_app_main_starts_background_uncertainty(monkeypatch):
    fake = FakeStreamlit(upload=object(), checkbox_values=[False])
    monkeypatch.setattr(app_ui, "st", fake)
    payload = {
        "results": sample_results(),
        "traces": sample_traces(),
        "diagnostics": sample_diagnostics(),
        "load_meta": {"warnings": [], "row_count": 3, "file_hash": "abc"},
        "uncertainty_state": "pending",
    }
    monkeypatch.setattr(app_ui, "run_pipeline", lambda upload, progress_callback=None: payload)
    monkeypatch.setattr(app_ui, "_resolve_uncertainty_future", lambda payload: (payload, None))
    started = {"called": False}
    monkeypatch.setattr(app_ui, "_maybe_start_uncertainty_job", lambda file_hash: started.__setitem__("called", True))
    monkeypatch.setattr(app_ui, "render_overview", lambda results, traces: None)
    monkeypatch.setattr(app_ui, "render_player_detail", lambda results, traces, diagnostics: None)
    monkeypatch.setattr(app_ui, "render_diagnostics", lambda payload_arg: None)
    app_ui.main()
    assert started["called"] is True
    assert any(call[0] == "info" and "Player profiles are ready" in call[1] for call in fake.calls)
    assert any(call[0] == "caption" and "Confidence status: running." in call[1] for call in fake.calls)


def test_app_main_shows_advanced_diagnostics_when_enabled(monkeypatch):
    fake = FakeStreamlit(upload=object(), checkbox_values=[True])
    monkeypatch.setattr(app_ui, "st", fake)
    payload = {
        "results": sample_results(),
        "traces": sample_traces(),
        "diagnostics": sample_diagnostics(),
        "load_meta": {"warnings": [], "row_count": 3, "file_hash": "abc"},
        "uncertainty_state": "complete",
    }
    monkeypatch.setattr(app_ui, "run_pipeline", lambda upload, progress_callback=None: payload)
    monkeypatch.setattr(app_ui, "_resolve_uncertainty_future", lambda payload: (payload, None))
    called = {"diag": False}
    monkeypatch.setattr(app_ui, "render_overview", lambda results, traces: None)
    monkeypatch.setattr(app_ui, "render_player_detail", lambda results, traces, diagnostics: None)
    monkeypatch.setattr(app_ui, "render_diagnostics", lambda payload_arg: called.__setitem__("diag", True))
    app_ui.main()
    assert called["diag"] is True
