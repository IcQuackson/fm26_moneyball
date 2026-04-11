from __future__ import annotations

import io

import pandas as pd
import streamlit as st


def render_overview(results: pd.DataFrame) -> None:
    st.subheader("Cohort Overview")
    if results.empty:
        st.info("No eligible player-role rows were produced from the upload.")
        return

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
    if selected_role != "All":
        filtered = filtered[filtered["broad_role"] == selected_role]
    if selected_club != "All":
        filtered = filtered[filtered["club"] == selected_club]
    filtered = filtered[filtered["age"].between(age_range[0], age_range[1], inclusive="both")]
    if minutes_range is not None:
        filtered = filtered[filtered["minutes"].between(minutes_range[0], minutes_range[1], inclusive="both")]

    summary = filtered[["player", "club", "age", "minutes", "performance_score", "cost_score", "value_gap_score", "uncertainty_score"]]
    st.dataframe(summary.sort_values("value_gap_score", ascending=False), use_container_width=True)

    buffer = io.StringIO()
    summary.to_csv(buffer, index=False)
    st.download_button("Export filtered table to CSV", data=buffer.getvalue(), file_name="fm26_cohort_overview.csv")

    chart_data = filtered[["player", "cost_score", "performance_score", "minutes", "uncertainty_score", "broad_role"]].dropna()
    if not chart_data.empty:
        st.vega_lite_chart(
            chart_data,
            {
                "mark": {"type": "circle", "tooltip": True},
                "encoding": {
                    "x": {"field": "cost_score", "type": "quantitative", "title": "Cost Score"},
                    "y": {"field": "performance_score", "type": "quantitative", "title": "Performance Score"},
                    "size": {"field": "minutes", "type": "quantitative", "title": "Minutes"},
                    "color": {"field": "uncertainty_score", "type": "quantitative", "title": "Uncertainty Score"},
                    "tooltip": [
                        {"field": "player", "type": "nominal"},
                        {"field": "broad_role", "type": "nominal", "title": "Role"},
                        {"field": "minutes", "type": "quantitative"},
                        {"field": "performance_score", "type": "quantitative"},
                        {"field": "cost_score", "type": "quantitative"},
                        {"field": "uncertainty_score", "type": "quantitative"},
                    ],
                },
            },
            use_container_width=True,
        )
