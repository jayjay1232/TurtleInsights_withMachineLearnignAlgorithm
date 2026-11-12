"""Nesting Location Forecast – 12-month outlook with ranked barangays."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.theme import COLORS, chart_layout
from utils.data_loader import BARANGAY_MAPPING, SHORT_NAMES
from utils.models import (
    get_or_train_models,
    forecast_location,
    evaluate_location_model,
)


def _rank_barangays(yhat: float, top_n: int = 3):
    """Rank codes 0–11 by closeness to continuous yhat (does not change the model)."""
    scores = []
    for code in range(12):
        dist = abs(float(yhat) - code)
        # similarity: closer code = higher score
        score = 1.0 / (1.0 + dist)
        scores.append((code, dist, score))
    scores.sort(key=lambda x: x[1])  # ascending distance
    out = []
    for rank, (code, dist, score) in enumerate(scores[:top_n], start=1):
        out.append({
            "rank": rank,
            "code": code,
            "barangay": BARANGAY_MAPPING.get(code, "Unknown"),
            "short": SHORT_NAMES.get(code, str(code)),
            "distance": dist,
            "score": score,
        })
    return out


def render(df: pd.DataFrame):
    st.markdown(
        """
        <div class="main-header">
            <h1>📍 Nesting Location Forecast</h1>
            <p>12-month barangay outlook from the original location Prophet model</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df is None or df.empty:
        st.markdown(
            '<div class="info-box"><strong>No dataset loaded.</strong> Upload an Excel file from the sidebar.</div>',
            unsafe_allow_html=True,
        )
        return

    if "L_TAGNUM" not in df.columns:
        st.error("This page needs **L_TAGNUM** (location code 0–11). Your original dataset includes this column.")
        return

    st.markdown(
        """
        <div class="insight-box">
            <strong> What this means in simple terms:</strong>
           The model predicts which barangay is most likely to be affected each month. It also shows the 2 other barangays that are closest to the predicted result as possible alternatives.
           This helps users understand the most likely location forecast and other locations that may also be worth monitoring.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c, col_d = st.columns([1.2, 1.2, 1.2, 1.8])
    with col_a:
        horizon = st.slider("Months to forecast", 6, 24, 12, key="loc_horizon")
    with col_b:
        top_n = st.selectbox("Barangays per month", options=[1, 2, 3], index=2, key="loc_topn")
    with col_c:
        force = st.checkbox("Force retrain", value=False, key="loc_force")
    with col_d:
        st.caption("Core model unchanged: monthly avg L_TAGNUM → yhat → nearest codes.")

    try:
        with st.spinner("Loading model…"):
            _, loc_model, _, loc_data = get_or_train_models(df, force_retrain=force)
    except Exception as e:
        st.error(f"Model preparation failed: {e}")
        st.info("Place `prophet_model_location_last.pkl` in `models/`, or retrain from Upload & Retrain.")
        return

    if loc_model is None or loc_data is None or loc_data.empty:
        st.warning("Not enough data to run the location model.")
        return

    metrics, _ = evaluate_location_model(loc_model, loc_data)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Training months", len(loc_data))
    if metrics:
        m2.metric("MAE (hold-out)", f"{metrics.get('MAE', 0):.2f}")
        m3.metric("RMSE (hold-out)", f"{metrics.get('RMSE', 0):.2f}")
        exact = metrics.get("Exact@code %")
        m4.metric("Exact code hit", f"{exact:.0f}%" if exact is not None else "—")

    st.markdown('<div class="section-card"><div class="section-title">Generate location outlook</div>', unsafe_allow_html=True)
    if st.button("Predict barangays (full horizon)", type="primary", key="do_loc_pred"):
        st.session_state["loc_run_forecast"] = True
    st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state.get("loc_run_forecast"):
        st.info("Click **Predict barangays (full horizon)** to generate the multi-month table.")
        # still show historical chart lightly
    try:
        with st.spinner("Generating outlook…"):
            forecast = forecast_location(loc_model, periods=horizon, prophet_data=loc_data)
    except Exception as e:
        st.error(f"Location forecast failed: {e}")
        return

    if forecast is None or forecast.empty:
        return

    future_mask = forecast["ds"] > loc_data["ds"].max()
    future = forecast.loc[future_mask].copy()
    if future.empty:
        st.warning("No future rows in forecast.")
        return

    # Build ranked rows
    rows = []
    for _, r in future.iterrows():
        ranks = _rank_barangays(float(r["yhat"]), top_n=int(top_n))
        primary = ranks[0]
        row = {
            "Date": pd.to_datetime(r["ds"]).strftime("%b %Y"),
            "Year": int(pd.to_datetime(r["ds"]).year),
            "Raw score": round(float(r["yhat"]), 2),
            "Primary code": primary["code"],
            "Primary barangay": primary["barangay"],
        }
        for item in ranks:
            row[f"#{item['rank']} place"] = item["short"]
            row[f"#{item['rank']} full name"] = item["barangay"]
            row[f"#{item['rank']} code"] = item["code"]
        rows.append(row)
    result_df = pd.DataFrame(rows)

    st.markdown('<div class="section-card"><div class="section-title">Multi-month location outlook</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=loc_data["ds"], y=loc_data["y"],
        mode="lines+markers", name="Historical avg code",
        line=dict(color=COLORS["deep_ocean"], width=2), marker=dict(size=5),
    ))
    fig.add_trace(go.Scatter(
        x=future["ds"], y=future["yhat"],
        mode="lines+markers", name="Forecast (raw yhat)",
        line=dict(color=COLORS["bright_sea"], width=2, dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        x=future["ds"], y=future["predicted_l_tagnum"],
        mode="markers", name="Primary rounded code",
        marker=dict(size=10, color=COLORS["sand"], symbol="diamond"),
    ))
    fig.update_layout(
        margin=dict(l=40, r=20, t=30, b=40),
        plot_bgcolor="rgba(255,255,255,1)",
        paper_bgcolor="rgba(255,255,255,0)",
        height=380,
        font=dict(color="#0A2647", size=13),
        xaxis=dict(
            title=dict(text="Date", font=dict(color="#0A2647", size=13)),
            tickfont=dict(color="#0A2647", size=12),
            gridcolor="rgba(10,38,71,0.12)",
            linecolor="#0A2647",
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text="L_TAGNUM (0–11)", font=dict(color="#0A2647", size=13)),
            tickfont=dict(color="#0A2647", size=12),
            gridcolor="rgba(10,38,71,0.12)",
            linecolor="#0A2647",
            zeroline=False,
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, x=0,
            font=dict(color="#0A2647", size=12),
            bgcolor="rgba(255,255,255,0.9)",
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Year filter for table
    years = sorted(result_df["Year"].unique().tolist())
    sel_years = st.multiselect("Show years in table", options=years, default=years, key="loc_table_years")
    show = result_df[result_df["Year"].isin(sel_years)] if sel_years else result_df

    # Compact columns for display
    display_cols = ["Date", "Year", "Raw score", "Primary barangay", "Primary code"]
    for i in range(1, int(top_n) + 1):
        col = f"#{i} place"
        if col in show.columns:
            display_cols.append(col)

    st.dataframe(show[display_cols], use_container_width=True, hide_index=True)

    if not show.empty:
        top = show.iloc[0]
        alt = ", ".join(str(top.get(f"#{i} place", "")) for i in range(2, int(top_n) + 1) if top.get(f"#{i} place"))
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>First forecast month ({top['Date']}):</strong>
                primary site <strong>{top['Primary barangay']}</strong>
                {f" · also nearby: {alt}" if alt else ""}.
                Rankings are nearest codes to the same model score — MAE/RMSE above still evaluate the primary rounded prediction.
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
