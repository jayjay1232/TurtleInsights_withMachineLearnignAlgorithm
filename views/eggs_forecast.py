"""Eggs Laid Forecast – with flexible year targeting."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.theme import COLORS, chart_layout
from utils.models import (
    get_or_train_models,
    forecast_eggs,
    evaluate_eggs_model,
    prepare_eggs_data,
)


def render(df: pd.DataFrame):
    st.markdown(
        """
        <div class="main-header">
            <h1>🥚 Eggs Laid Forecast</h1>
            <p>Predicts the average number of eggs per nest for future months</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df is None or df.empty:
        st.markdown(
            '<div class="info-box"><strong>No dataset loaded.</strong> Upload an Excel file from the sidebar or use Upload & Retrain.</div>',
            unsafe_allow_html=True,
        )
        return

    if "NO. OF EGGS LAID" not in df.columns:
        st.error("This page needs a column named **NO. OF EGGS LAID**.")
        return

    st.markdown(
        """
        <div class="insight-box">
            <strong>What this means in plain language:</strong>
            The chart shows how many eggs turtles usually lay each month, and the dashed line
            is the model’s best guess for the next months. The shaded band is the uncertainty range —
            wider band = less certainty. Choose a <em>target year</em> to stretch the forecast
            far enough to cover that year when you add newer datasets later.
        </div>
        """,
        unsafe_allow_html=True,
    )

    data_max_year = int(df["DATE LAID"].dt.year.max()) if "DATE LAID" in df.columns else 2024
    default_target = max(data_max_year + 1, 2025)

    col_a, col_b, col_c, col_d = st.columns([1.2, 1.2, 1.3, 1.8])
    with col_a:
        target_year = st.number_input(
            "Target year",
            min_value=2015,
            max_value=2040,
            value=int(default_target),
            step=1,
            key="eggs_target_year",
            help="Forecast will extend at least through December of this year.",
        )
    with col_b:
        extra_months = st.slider("Extra months after target year", 0, 12, 0, key="eggs_extra")
    with col_c:
        force = st.checkbox("Force retrain from current data", value=False, key="eggs_force")
    with col_d:
        st.caption("Original model: yearly + monthly + quarterly seasonality, lag & EMA features.")

    try:
        with st.spinner("Loading model…"):
            eggs_model, _, eggs_data, _ = get_or_train_models(df, force_retrain=force)
    except Exception as e:
        st.error(f"Model preparation failed: {e}")
        st.info("Place your original `prophet_finaleggslaidmodel.pkl` in the `models/` folder, or retrain from Upload & Retrain.")
        return

    if eggs_model is None or eggs_data is None or eggs_data.empty:
        st.warning("Not enough monthly data to run the eggs model (need several months after lag features).")
        preview = prepare_eggs_data(df)
        if not preview.empty:
            st.dataframe(preview.head(15), use_container_width=True)
        return

    last_hist = pd.to_datetime(eggs_data["ds"].max())
    # months from month after last history through Dec of target year (+ optional extra)
    end_date = pd.Timestamp(year=int(target_year), month=12, day=1) + pd.DateOffset(months=int(extra_months))
    # number of month-starts strictly after last_hist up to end_date
    periods = 0
    cursor = last_hist + pd.offsets.MonthBegin(1)
    while cursor <= end_date:
        periods += 1
        cursor += pd.offsets.MonthBegin(1)
    periods = max(periods, 3)
    periods = min(periods, 120)  # safety cap

    metrics, _ = evaluate_eggs_model(eggs_model, eggs_data)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Training months", len(eggs_data))
    m2.metric("History ends", last_hist.strftime("%b %Y"))
    m3.metric("Forecast months", periods)
    if metrics:
        m4.metric("MAE (hold-out)", f"{metrics.get('MAE', 0):.3f}")
        mape = metrics.get("MAPE")
        m5.metric("MAPE (hold-out)", f"{mape:.2f}%" if mape is not None and not np.isnan(mape) else "—")

    try:
        with st.spinner("Generating forecast…"):
            forecast = forecast_eggs(eggs_model, eggs_data, periods=periods)
    except Exception as e:
        st.error(f"Forecast failed: {e}")
        st.info("Try Force retrain, or replace the PKL in models/ with your original file.")
        return

    if forecast is None or forecast.empty:
        st.error("Forecast returned no rows.")
        return

    future_mask = forecast["ds"] > eggs_data["ds"].max()
    future_df = forecast.loc[future_mask, ["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

    # Optional year filter for the table display
    years_in_future = sorted(future_df["ds"].dt.year.unique().tolist()) if not future_df.empty else []
    show_years = st.multiselect(
        "Show table years",
        options=years_in_future,
        default=years_in_future,
        key="eggs_table_years",
        help="Pick which forecast years appear in the numbers table below.",
    )

    st.markdown('<div class="section-card"><div class="section-title">Monthly average eggs — history & forecast</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=eggs_data["ds"], y=eggs_data["y"],
        mode="lines+markers", name="Historical average",
        line=dict(color=COLORS["deep_ocean"], width=2.5), marker=dict(size=5),
    ))
    fig.add_trace(go.Scatter(
        x=forecast.loc[future_mask, "ds"], y=forecast.loc[future_mask, "yhat"],
        mode="lines+markers", name="Forecast",
        line=dict(color=COLORS["bright_sea"], width=2.5, dash="dash"), marker=dict(size=6),
    ))
    if "yhat_lower" in forecast.columns and "yhat_upper" in forecast.columns:
        fig.add_trace(go.Scatter(
            x=forecast.loc[future_mask, "ds"].tolist() + forecast.loc[future_mask, "ds"].tolist()[::-1],
            y=forecast.loc[future_mask, "yhat_upper"].tolist() + forecast.loc[future_mask, "yhat_lower"].tolist()[::-1],
            fill="toself", fillcolor="rgba(20, 145, 155, 0.18)",
            line=dict(color="rgba(255,255,255,0)"), name="Uncertainty", hoverinfo="skip",
        ))
    fig.add_trace(go.Scatter(
        x=forecast.loc[~future_mask, "ds"], y=forecast.loc[~future_mask, "yhat"],
        mode="lines", name="Model fit",
        line=dict(color=COLORS["sand"], width=1.5, dash="dot"), opacity=0.7,
    ))
    fig.update_layout(
        margin=dict(l=40, r=20, t=30, b=40),
        plot_bgcolor="rgba(255,255,255,1)",
        paper_bgcolor="rgba(255,255,255,0)",
        height=420,
        font=dict(color="#0A2647", size=13),
        xaxis=dict(
            title=dict(text="Date", font=dict(color="#0A2647", size=13)),
            tickfont=dict(color="#0A2647", size=12),
            gridcolor="rgba(10,38,71,0.12)",
            linecolor="#0A2647",
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text="Average eggs laid", font=dict(color="#0A2647", size=13)),
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
    st.markdown("</div>", unsafe_allow_html=True)

    table = future_df.copy()
    if show_years:
        table = table[table["ds"].dt.year.isin(show_years)]
    table = table.rename(columns={
        "ds": "Date",
        "yhat": "Predicted avg eggs",
        "yhat_lower": "Lower",
        "yhat_upper": "Upper",
    })
    table["Year"] = pd.to_datetime(table["Date"]).dt.year
    table["Date"] = pd.to_datetime(table["Date"]).dt.strftime("%b %Y")
    for c in ["Predicted avg eggs", "Lower", "Upper"]:
        table[c] = table[c].round(1)

    if not table.empty:
        next_val = table.iloc[0]["Predicted avg eggs"]
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>Quick takeaway:</strong> First forecast month shows about
                <strong>{next_val:.0f}</strong> eggs on average. Table covers years
                <strong>{', '.join(str(y) for y in sorted(table['Year'].unique()))}</strong>
                based on your target year and current history ending <strong>{last_hist.strftime('%b %Y')}</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-card"><div class="section-title">Forecast table</div>', unsafe_allow_html=True)
    st.dataframe(
        table[["Date", "Year", "Predicted avg eggs", "Lower", "Upper"]],
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
