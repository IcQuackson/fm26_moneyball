from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from src.ui.presentation import confidence_label, format_metric_label, format_role_label, percentile_band, percentile_style

def _category_score_columns(results: pd.DataFrame) -> list[str]:
    excluded = {"performance_score", "cost_score", "value_gap_score", "uncertainty_score"}
    return [
        column
        for column in results.columns
        if column.endswith("__score") and column not in excluded
    ]


def render_overview(results: pd.DataFrame) -> None:
    st.subheader("Scout Board")
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

    headline_cols = st.columns(4)
    headline_cols[0].metric("Profiles", str(len(filtered)))
    headline_cols[1].metric("Average Age", f"{filtered['age'].mean():.1f}" if not filtered.empty else "NA")
    headline_cols[2].metric("Avg Category Score", f"{filtered['category_mean_score'].mean():.1f}" if filtered['category_mean_score'].notna().any() else "NA")
    headline_cols[3].metric("Best Value Gems", str(int((filtered["value_gap_score"] >= 75).sum())) if filtered["value_gap_score"].notna().any() else "0")

    scout_view = filtered[
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
    scout_view = scout_view.rename(
        columns={
            "player": "Player",
            "division": "Division",
            "club": "Club",
            "broad_role": "Role",
            "age": "Age",
            "minutes": "Minutes",
            "best_category": "Best Trait",
            "best_category_score": "Best Trait Pctl",
            "category_mean_score": "Overall Profile Pctl",
            "cost_score": "Cost Pctl",
            "value_gap_score": "Value For Money",
            "uncertainty_score": "Risk",
        }
    )
    scout_view["Role"] = scout_view["Role"].map(format_role_label)
    scout_view["Best Trait"] = scout_view["Best Trait"].map(format_metric_label)
    scout_view = scout_view.sort_values("Value For Money", ascending=False)
    scout_styler = scout_view.style.map(percentile_style, subset=["Best Trait Pctl", "Overall Profile Pctl", "Cost Pctl", "Value For Money", "Risk"])
    st.dataframe(scout_styler, use_container_width=True)

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
    st.download_button("Export scout board to CSV", data=buffer.getvalue(), file_name="fm26_cohort_overview.csv")

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

    if category_score_cols and not filtered.empty:
        st.markdown("**Category Strength Snapshot**")
        category_snapshot = (
            filtered[category_score_cols]
            .rename(columns=lambda value: format_metric_label(value.replace("__score", "")))
            .mean(axis=0)
            .sort_values(ascending=False)
        )
        st.bar_chart(category_snapshot)

    if not filtered.empty:
        st.markdown("**Quick Read**")
        quick_read = filtered[["player", "best_category", "best_category_score", "value_gap_score", "uncertainty_score"]].copy()
        quick_read["best_category"] = quick_read["best_category"].map(format_metric_label)
        quick_read["trait_band"] = quick_read["best_category_score"].map(percentile_band)
        quick_read["value_band"] = quick_read["value_gap_score"].map(percentile_band)
        quick_read["confidence"] = quick_read["uncertainty_score"].map(lambda value: confidence_label(value)[0])
        quick_read_display = quick_read.rename(
                columns={
                    "player": "Player",
                    "best_category": "Standout Trait",
                    "best_category_score": "Trait Percentile",
                    "trait_band": "Trait Grade",
                    "value_gap_score": "Value For Money",
                    "value_band": "Value Grade",
                    "confidence": "Confidence",
                }
        )
        quick_read_styler = quick_read_display.style.map(percentile_style, subset=["Trait Percentile", "Value For Money"])
        st.dataframe(quick_read_styler, use_container_width=True)

    st.markdown("**League Category Rankings**")
    if selected_division == "All" or selected_role == "All":
        st.info("Select one Division and one Role to view category rankings inside that league cohort.")
    elif category_score_cols:
        ranking_category = st.selectbox(
            "Ranking Category",
            options=category_score_cols,
            format_func=lambda value: format_metric_label(value.replace("__score", "")),
        )
        ranking_frame = filtered[["player", "club", "minutes", ranking_category, "value_gap_score", "uncertainty_score"]].copy()
        ranking_frame = ranking_frame.rename(
            columns={
                "player": "Player",
                "club": "Club",
                "minutes": "Minutes",
                ranking_category: "Category Percentile",
                "value_gap_score": "Value For Money",
                "uncertainty_score": "Risk",
            }
        )
        ranking_frame["Rank"] = ranking_frame["Category Percentile"].rank(method="min", ascending=False)
        ranking_frame["Grade"] = ranking_frame["Category Percentile"].map(percentile_band)
        ranking_frame = ranking_frame.sort_values(["Rank", "Player"]).reset_index(drop=True)
        ranking_frame = ranking_frame[["Rank", "Player", "Club", "Minutes", "Category Percentile", "Grade", "Value For Money", "Risk"]]
        st.dataframe(
            ranking_frame.style.map(percentile_style, subset=["Category Percentile", "Value For Money", "Risk"]),
            use_container_width=True,
        )
