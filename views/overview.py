"""
Overview & Insights – Analytical Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.theme import COLORS, PLOTLY_CAT, PLOTLY_SEQ
from utils.data_loader import (
    get_filter_options, apply_filters, BARANGAY_MAPPING, SHORT_NAMES
)


AXIS_DARK = "#0A2647"


def _base_layout(**kwargs):
    layout = dict(
        margin=dict(l=40, r=24, t=28, b=40),
        plot_bgcolor="rgba(255,255,255,1)",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(color=AXIS_DARK, size=13),
        xaxis=dict(
            title_font=dict(color=AXIS_DARK, size=13),
            tickfont=dict(color=AXIS_DARK, size=12),
            gridcolor="rgba(10,38,71,0.12)",
            linecolor=AXIS_DARK,
            zeroline=False,
        ),
        yaxis=dict(
            title_font=dict(color=AXIS_DARK, size=13),
            tickfont=dict(color=AXIS_DARK, size=12),
            gridcolor="rgba(10,38,71,0.12)",
            linecolor=AXIS_DARK,
            zeroline=False,
        ),
        legend=dict(
            font=dict(color=AXIS_DARK, size=12),
            bgcolor="rgba(255,255,255,0.9)",
        ),
        coloraxis_colorbar=dict(
            tickfont=dict(color=AXIS_DARK),
            title_font=dict(color=AXIS_DARK),
        ),
    )
    for k, v in kwargs.items():
        if k in ("xaxis", "yaxis", "yaxis2", "legend", "margin") and isinstance(v, dict):
            base = dict(layout.get(k, {}))
            base.update(v)
            layout[k] = base
        else:
            layout[k] = v
    return layout


def _kpi_html(label: str, value: str, delta: str = "") -> str:
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


def render(df: pd.DataFrame):
    st.markdown(
        """
        <div class="main-header">
            <h1>🌊 Overview & Nesting Insights</h1>
            <p>Explore patterns in turtle nesting activity across La Union coastal barangays</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="insight-box">
            <strong>How to read this page:</strong>
            The cards show totals for nests, eggs, and hatchlings. Charts below answer simple questions:
            <em>When do turtles nest most?</em> · <em>Which barangays are busiest?</em> ·
            <em>Are hatching rates healthy?</em> Use the filters to focus on a year or place.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df is None or df.empty:
        st.markdown(
            """
            <div class="info-box">
                <strong>No dataset loaded.</strong><br>
                Please upload <code>FINALTURTLE_DATASET.xlsx</code> (or equivalent) using the sidebar uploader.
                The file should contain columns such as DATE LAID, NO. OF EGGS LAID, L_TAGNUM, etc.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    opts = get_filter_options(df)
    month_labels = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
    }

    with st.container():
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
        fcols = st.columns([1.4, 1.4, 2.2, 1.2])

        with fcols[0]:
            years = opts.get("years", [])
            sel_years = st.multiselect(
                "Year", options=years, default=years, key="ov_years",
            )
        with fcols[1]:
            months = opts.get("months", list(range(1, 13)))
            sel_months = st.multiselect(
                "Month",
                options=months,
                format_func=lambda m: month_labels.get(m, str(m)),
                default=months,
                key="ov_months",
            )
        with fcols[2]:
            locs = opts.get("locations", [])
            if not locs and "L_TAGNUM" not in df.columns:
                st.caption("No L_TAGNUM column — location filter disabled")
                sel_locs = None
            else:
                if not locs:
                    locs = list(range(12))
                sel_locs = st.multiselect(
                    "Barangay / Location",
                    options=locs,
                    format_func=lambda x: SHORT_NAMES.get(x, str(x)),
                    default=locs,
                    key="ov_locs",
                )
        with fcols[3]:
            st.write("")
            st.write("")
            if st.button("Reset Filters", key="ov_reset"):
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    filtered = apply_filters(
        df,
        years=sel_years or None,
        months=sel_months or None,
        locations=sel_locs or None,
    )

    if filtered.empty:
        st.warning("No records match the current filters. Try expanding your selection.")
        return

    total_nests = len(filtered)
    total_eggs = int(filtered["NO. OF EGGS LAID"].sum()) if "NO. OF EGGS LAID" in filtered.columns else 0
    avg_eggs = filtered["NO. OF EGGS LAID"].mean() if "NO. OF EGGS LAID" in filtered.columns else 0
    avg_hatch = filtered["HATCHING RATE"].mean() if "HATCHING RATE" in filtered.columns else None
    hatchlings = int(filtered["NO. OF HATCHLING RELEASED"].sum()) if "NO. OF HATCHLING RELEASED" in filtered.columns else 0
    unique_locs = filtered["L_TAGNUM"].nunique() if "L_TAGNUM" in filtered.columns else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(_kpi_html("Total Nests", f"{total_nests:,}"), unsafe_allow_html=True)
    with k2:
        st.markdown(_kpi_html("Total Eggs Laid", f"{total_eggs:,}"), unsafe_allow_html=True)
    with k3:
        st.markdown(_kpi_html("Avg Eggs / Nest", f"{avg_eggs:.1f}"), unsafe_allow_html=True)
    with k4:
        if avg_hatch is not None and not np.isnan(avg_hatch):
            display_h = f"{avg_hatch*100:.1f}%" if avg_hatch <= 1 else f"{avg_hatch:.1f}%"
            st.markdown(_kpi_html("Avg Hatching Rate", display_h), unsafe_allow_html=True)
        else:
            st.markdown(_kpi_html("Hatchlings Released", f"{hatchlings:,}"), unsafe_allow_html=True)
    with k5:
        st.markdown(_kpi_html("Active Locations", f"{unique_locs}"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-card"><div class="section-title">Monthly Nesting Activity</div>', unsafe_allow_html=True)
        if "MONTH" in filtered.columns:
            monthly_counts = (
                filtered.groupby("MONTH").size().reindex(range(1, 13), fill_value=0).reset_index(name="Nests")
            )
            monthly_counts["Month"] = monthly_counts["MONTH"].map(month_labels)
            fig = px.bar(
                monthly_counts, x="Month", y="Nests",
                color_discrete_sequence=[COLORS["sea_teal"]],
            )
            fig.update_layout(_base_layout(
                height=320,
                xaxis=dict(title=""),
                yaxis=dict(title="Number of Nests"),
            ))
            fig.update_traces(marker_line_width=0, opacity=0.9)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-card"><div class="section-title">Nesting by Barangay</div>', unsafe_allow_html=True)
        if "L_TAGNUM" in filtered.columns:
            loc_counts = (
                filtered.groupby(["L_TAGNUM", "BARANGAY_SHORT"]).size()
                .reset_index(name="Nests").sort_values("Nests", ascending=True)
            )
            fig = px.bar(
                loc_counts, x="Nests", y="BARANGAY_SHORT", orientation="h",
                color="Nests", color_continuous_scale=PLOTLY_SEQ,
            )
            fig.update_layout(_base_layout(
                height=320,
                xaxis=dict(title="Number of Nests"),
                yaxis=dict(title=""),
                coloraxis_showscale=False,
            ))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="section-card"><div class="section-title">Eggs Laid Over Time</div>', unsafe_allow_html=True)
        if "DATE LAID" in filtered.columns and "NO. OF EGGS LAID" in filtered.columns:
            ts = (
                filtered.set_index("DATE LAID")
                .resample("ME")["NO. OF EGGS LAID"]
                .agg(["sum", "mean", "count"])
                .reset_index()
            )
            ts.columns = ["Date", "Total Eggs", "Avg Eggs", "Nests"]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ts["Date"], y=ts["Total Eggs"], mode="lines+markers", name="Total Eggs",
                line=dict(color=COLORS["sea_teal"], width=2.5), marker=dict(size=6),
            ))
            fig.add_trace(go.Scatter(
                x=ts["Date"], y=ts["Avg Eggs"], mode="lines", name="Avg per Nest",
                line=dict(color=COLORS["sand"], width=2, dash="dot"), yaxis="y2",
            ))
            fig.update_layout(_base_layout(
                height=340,
                yaxis=dict(title="Total Eggs"),
                yaxis2=dict(
                    title="Avg Eggs / Nest",
                    overlaying="y",
                    side="right",
                    title_font=dict(color=AXIS_DARK, size=12),
                    tickfont=dict(color=AXIS_DARK, size=11),
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=AXIS_DARK, size=12)),
                hovermode="x unified",
            ))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="section-card"><div class="section-title">Yearly Comparison</div>', unsafe_allow_html=True)
        if "YEAR" in filtered.columns:
            yearly = (
                filtered.groupby("YEAR")
                .agg(
                    Nests=("DATE LAID", "count"),
                    Eggs=("NO. OF EGGS LAID", "sum") if "NO. OF EGGS LAID" in filtered.columns else ("DATE LAID", "count"),
                )
                .reset_index()
            )
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=yearly["YEAR"].astype(str), y=yearly["Nests"], name="Nests",
                marker_color=COLORS["bright_sea"], opacity=0.85,
            ))
            if "Eggs" in yearly.columns and yearly["Eggs"].sum() > yearly["Nests"].sum():
                fig.add_trace(go.Scatter(
                    x=yearly["YEAR"].astype(str), y=yearly["Eggs"], name="Total Eggs",
                    mode="lines+markers",
                    marker=dict(size=8, color=COLORS["sand"]),
                    line=dict(width=2.5, color=COLORS["coral"]),
                    yaxis="y2",
                ))
                fig.update_layout(yaxis2=dict(
                    title="Total Eggs", overlaying="y", side="right",
                    title_font=dict(color=AXIS_DARK), tickfont=dict(color=AXIS_DARK),
                ))
            fig.update_layout(_base_layout(
                height=340,
                yaxis=dict(title="Number of Nests"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=AXIS_DARK, size=12)),
                barmode="group",
            ))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">Deeper Insights</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["Eggs Distribution", "Hatching Performance", "Seasonality Heatmap", "Data Table"])

    with tab1:
        if "NO. OF EGGS LAID" in filtered.columns:
            fig = px.histogram(
                filtered, x="NO. OF EGGS LAID", nbins=25,
                color_discrete_sequence=[COLORS["sea_teal"]],
                labels={"NO. OF EGGS LAID": "Eggs per Nest"},
            )
            fig.update_layout(_base_layout(height=360, yaxis=dict(title="Frequency")))
            mean_val = filtered["NO. OF EGGS LAID"].mean()
            fig.add_vline(
                x=mean_val, line_dash="dash", line_color=COLORS["coral"],
                annotation_text=f"Mean: {mean_val:.1f}", annotation_position="top",
                annotation_font=dict(color=AXIS_DARK),
            )
            st.plotly_chart(fig, use_container_width=True)
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Min Eggs", int(filtered["NO. OF EGGS LAID"].min()))
            s2.metric("Median", f"{filtered['NO. OF EGGS LAID'].median():.0f}")
            s3.metric("Mean", f"{filtered['NO. OF EGGS LAID'].mean():.1f}")
            s4.metric("Max Eggs", int(filtered["NO. OF EGGS LAID"].max()))

    with tab2:
        if "HATCHING RATE" in filtered.columns or "NO. OF HATCHLING RELEASED" in filtered.columns:
            col_a, col_b = st.columns(2)
            with col_a:
                if "HATCHING RATE" in filtered.columns:
                    rate = filtered["HATCHING RATE"].dropna()
                    if rate.max() <= 1.5:
                        rate = rate * 100
                    fig = px.box(
                        x=rate, labels={"x": "Hatching Rate (%)"},
                        color_discrete_sequence=[COLORS["bright_sea"]],
                    )
                    fig.update_layout(_base_layout(height=300))
                    st.plotly_chart(fig, use_container_width=True)
            with col_b:
                if "NO. OF HATCHLING RELEASED" in filtered.columns and "NO. OF EGGS LAID" in filtered.columns:
                    tmp = filtered.dropna(subset=["NO. OF HATCHLING RELEASED", "NO. OF EGGS LAID"]).copy()
                    fig = px.scatter(
                        tmp,
                        x="NO. OF EGGS LAID",
                        y="NO. OF HATCHLING RELEASED",
                        color="BARANGAY_SHORT" if "BARANGAY_SHORT" in tmp.columns else None,
                        color_discrete_sequence=PLOTLY_CAT,
                        opacity=0.7,
                        labels={
                            "NO. OF EGGS LAID": "Eggs Laid",
                            "NO. OF HATCHLING RELEASED": "Hatchlings",
                        },
                    )
                    fig.update_layout(_base_layout(height=300))
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Hatching rate / hatchling columns not present in this dataset.")

    with tab3:
        if "YEAR" in filtered.columns and "MONTH" in filtered.columns:
            heat = filtered.groupby(["YEAR", "MONTH"]).size().reset_index(name="Nests")
            heat_pivot = heat.pivot(index="MONTH", columns="YEAR", values="Nests").fillna(0)
            heat_pivot.index = [month_labels.get(m, m) for m in heat_pivot.index]
            fig = px.imshow(
                heat_pivot,
                color_continuous_scale=["#E8F6F3", "#14919B", "#0A2647"],
                aspect="auto",
                labels=dict(color="Nests"),
            )
            fig.update_layout(_base_layout(
                height=380,
                xaxis=dict(title="Year"),
                yaxis=dict(title="Month"),
            ))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need YEAR and MONTH for seasonality heatmap.")

    with tab4:
        show_cols = [c for c in [
            "TURTLE_NUM", "DATE LAID", "NO. OF EGGS LAID",
            "NO. OF HATCHLING RELEASED", "UNHATCHED EGGS", "HATCHING RATE",
            "BARANGAY", "L_TAGNUM", "YEAR", "MONTH_NAME",
        ] if c in filtered.columns]
        st.dataframe(
            filtered[show_cols].sort_values("DATE LAID", ascending=False),
            use_container_width=True,
            height=400,
        )
        st.caption(f"Showing {len(filtered):,} filtered records")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="app-footer">
            Turtle Analytical Insights • La Union Coastal Nesting Sites
        </div>
        """,
        unsafe_allow_html=True,
    )
