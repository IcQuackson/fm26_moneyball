from __future__ import annotations

import io

import pandas as pd
import streamlit as st


def _category_score_columns(results: pd.DataFrame) -> list[str]:
    excluded = {"performance_score", "cost_score", "value_gap_score", "uncertainty_score"}
    return [
        column
        for column in results.columns
        if column.endswith("__score") and column not in excluded
    ]


def render_overview(results: pd.DataFrame) -> None:
    st.subheader("Cohort Overview")
    if results.empty:
        st.info("No eligible player-role rows were produced from the upload.")
        return

    division_options = ["All"] + sorted(results["division"].dropna().unique().tolist())
    selected_division = st.selectbox("Division", division_options, index=0)
    role_options = ["All"] + sorted(results["broad_role"].dropna().unique().tolist())
    selected_role = st.selectbox("Role", role_options, index=0)
    club_options = ["All"] + sorted(results["club"].dropna().unique().tolist())
    selected_club = st.selectbox("Club", club_options, index=0)
    age_range = st.slider("Age band", 15, 45, (15, 45))
    max_minutes = int(results["minutes"].fillna(0).max())
    if max_minutes > 0:
        minutes_range = st.slider(
            "Minutes band",
            0,
            max_minutes,
            (0, max_minutes),
        )
    else:
        minutes_range = None
        st.info("Minutes filter is unavailable because all rows have zero or missing minutes.")

    filtered = results.copy()
    if selected_division != "All":
        filtered = filtered[filtered["division"] == selected_division]
    if selected_role != "All":
        filtered = filtered[filtered["broad_role"] == selected_role]
    if selected_club != "All":
        filtered = filtered[filtered["club"] == selected_club]
    filtered = filtered[filtered["age"].between(age_range[0], age_range[1], inclusive="both")]
    if minutes_range is not None:
        filtered = filtered[filtered["minutes"].between(minutes_range[0], minutes_range[1], inclusive="both")]

    category_score_cols = _category_score_columns(filtered)
    if category_score_cols:
        category_frame = filtered[category_score_cols].copy()
        filtered["category_mean_score"] = category_frame.mean(axis=1, skipna=True)
        filtered["best_category"] = category_frame.idxmax(axis=1).str.replace("__score", "", regex=False)
        filtered["best_category_score"] = category_frame.max(axis=1, skipna=True)
    else:
        filtered["category_mean_score"] = pd.NA
        filtered["best_category"] = pd.NA
        filtered["best_category_score"] = pd.NA

    summary = filtered[
        [
            "player",
            "division",
            "club",
            "broad_role",
            "age",
            "minutes",
            "best_category",
            "best_category_score",
            "category_mean_score",
            "cost_score",
            "value_gap_score",
            "uncertainty_score",
        ]
    ]
    st.dataframe(summary.sort_values("value_gap_score", ascending=False), use_container_width=True)

    buffer = io.StringIO()
    export_frame = filtered[
        [
            "player",
            "division",
            "club",
            "broad_role",
            "age",
            "minutes",
            "best_category",
            "best_category_score",
            "category_mean_score",
            "performance_score",
            "cost_score",
            "value_gap_score",
            "uncertainty_score",
        ]
        + category_score_cols
    ]
    export_frame.to_csv(buffer, index=False)
    st.download_button("Export filtered table to CSV", data=buffer.getvalue(), file_name="fm26_cohort_overview.csv")

    chart_columns = ["player", "cost_score", "category_mean_score", "minutes", "broad_role", "division", "uncertainty_score"]
    chart_data = filtered[chart_columns].dropna(subset=["player", "cost_score", "category_mean_score", "minutes", "broad_role", "division"])
    if not chart_data.empty:
        encoding = {
            "x": {"field": "cost_score", "type": "quantitative", "title": "Cost Score"},
            "y": {"field": "category_mean_score", "type": "quantitative", "title": "Category Mean Score"},
            "size": {"field": "minutes", "type": "quantitative", "title": "Minutes"},
            "tooltip": [
                {"field": "player", "type": "nominal"},
                {"field": "division", "type": "nominal"},
                {"field": "broad_role", "type": "nominal", "title": "Role"},
                {"field": "minutes", "type": "quantitative"},
                {"field": "category_mean_score", "type": "quantitative"},
                {"field": "cost_score", "type": "quantitative"},
            ],
        }
        if chart_data["uncertainty_score"].notna().any():
            encoding["color"] = {"field": "uncertainty_score", "type": "quantitative", "title": "Uncertainty Score"}
            encoding["tooltip"].append({"field": "uncertainty_score", "type": "quantitative"})
        st.vega_lite_chart(
            chart_data,
            {
                "mark": {"type": "circle", "tooltip": True},
                "encoding": encoding,
            },
            use_container_width=True,
        )
