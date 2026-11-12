"""Upload & Retrain – load a new dataset and rebuild Prophet models with reliability metrics."""

import streamlit as st
import pandas as pd
from utils.models import (
    retrain_all,
    prepare_eggs_data,
    prepare_location_data,
    evaluate_eggs_model,
    evaluate_location_model,
    MODELS_DIR,
    EGGS_PKL_CANDIDATES,
    LOC_PKL_CANDIDATES,
)
from utils.data_loader import load_turtle_data


def _reliability_label(mae, rmse, kind="eggs", exact=None):
    """Plain-language band from hold-out error."""
    if mae is None:
        return "Not available", "—"
    if kind == "eggs":
        if mae < 5 and (rmse is None or rmse < 8):
            return "Strong", "Errors are small vs typical egg counts."
        if mae < 15:
            return "Acceptable", "Usable for planning; watch wide uncertainty bands."
        return "Weak", "Consider more data or checking data quality before relying on forecasts."
    # location codes 0–11 — prefer exact-code rate when present
    if exact is not None:
        if exact >= 55 and mae < 1.25:
            return "Strong", "Often hits the correct barangay code on hold-out."
        if exact >= 35 or mae < 2.0:
            return "Acceptable", "Usually within 1–2 barangay codes; use top-3 list for planning."
        return "Weak", "Location signal is noisy; treat as directional guidance only."
    if mae < 1.0 and (rmse is None or rmse < 1.5):
        return "Strong", "Rounded location codes match hold-out closely."
    if mae < 2.0:
        return "Acceptable", "Usually within 1–2 barangay codes on hold-out."
    return "Weak", "Location signals are noisy; use rankings as guidance only."


def render(df: pd.DataFrame):
    st.markdown(
        """
        <div class="main-header">
            <h1>📂 Upload & Retrain</h1>
            <p>Add a new Excel dataset and rebuild both forecasting models</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="insight-box">
            <strong>When to use this page:</strong>
            After a new nesting season, upload the updated Excel file and click
            <em>Retrain both models</em>. Below the button you will see hold-out
            MAE / RMSE / MAPE so you can judge whether the refreshed models are still reliable.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-card"><div class="section-title">1. Upload dataset</div>', unsafe_allow_html=True)
    up = st.file_uploader(
        "Excel file with nesting records",
        type=["xlsx", "xls"],
        key="retrain_uploader",
        help="Required columns: DATE LAID, NO. OF EGGS LAID, L_TAGNUM",
    )
    if up is not None:
        try:
            new_df = load_turtle_data(up)
            if new_df is not None and not new_df.empty:
                st.session_state.turtle_df = new_df
                st.session_state.data_source = up.name
                df = new_df
                st.success(f"Loaded **{len(new_df):,}** records from `{up.name}`")
                missing = [c for c in ["DATE LAID", "NO. OF EGGS LAID", "L_TAGNUM"] if c not in new_df.columns]
                if missing:
                    st.warning(f"Missing columns after loading: {', '.join(missing)}. Check your header names.")
                else:
                    st.caption("Key columns found: DATE LAID, NO. OF EGGS LAID, L_TAGNUM ✓")
            else:
                st.error("Could not parse that file.")
        except Exception as e:
            st.error(f"Upload failed: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">2. Current data snapshot</div>', unsafe_allow_html=True)
    if df is None or df.empty:
        st.info("No data in memory yet. Upload a file above or place FINALTURTLE_DATASET.xlsx in the data/ folder.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records", f"{len(df):,}")
    if "DATE LAID" in df.columns:
        c2.metric("Date range", f"{df['DATE LAID'].min().date()} → {df['DATE LAID'].max().date()}")
    if "L_TAGNUM" in df.columns:
        c3.metric("Locations", df["L_TAGNUM"].nunique())
    if "NO. OF EGGS LAID" in df.columns:
        c4.metric("Total eggs", f"{int(df['NO. OF EGGS LAID'].sum()):,}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">3. Retrain models</div>', unsafe_allow_html=True)
    st.write(
        "Runs the same training steps as your original notebooks and overwrites PKL files "
        "in `models/` (project names + original notebook filenames)."
    )
    if st.button("🔄 Retrain both models", type="primary"):
        with st.spinner("Retraining eggs + location models… this can take up to a minute."):
            try:
                eggs_model, loc_model, eggs_data, loc_data = retrain_all(df)
                eggs_metrics, eggs_merged = evaluate_eggs_model(eggs_model, eggs_data)
                loc_metrics, loc_merged = evaluate_location_model(loc_model, loc_data)
                st.session_state["retrain_ok"] = True
                st.session_state["retrain_info"] = {
                    "eggs_months": len(eggs_data),
                    "loc_months": len(loc_data),
                    "eggs_ok": eggs_model is not None,
                    "loc_ok": loc_model is not None,
                    "eggs_metrics": eggs_metrics,
                    "loc_metrics": loc_metrics,
                }
                st.success("Retrain finished.")
            except Exception as e:
                st.session_state["retrain_ok"] = False
                st.error(f"Retrain failed: {e}")

    if st.session_state.get("retrain_ok"):
        info = st.session_state.get("retrain_info", {})
        st.markdown(
            f"""
            <div class="success-box">
                ✅ Eggs model: {"ready" if info.get("eggs_ok") else "skipped"}
                ({info.get("eggs_months", 0)} monthly points)<br>
                ✅ Location model: {"ready" if info.get("loc_ok") else "skipped"}
                ({info.get("loc_months", 0)} monthly points)
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### Hold-out reliability metrics (after retrain)")
        em = info.get("eggs_metrics") or {}
        lm = info.get("loc_metrics") or {}

        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Eggs MAE", f"{em['MAE']:.3f}" if em.get("MAE") is not None else "—")
        e2.metric("Eggs RMSE", f"{em['RMSE']:.3f}" if em.get("RMSE") is not None else "—")
        mape = em.get("MAPE")
        e3.metric("Eggs MAPE", f"{mape:.2f}%" if mape is not None else "—")
        band, note = _reliability_label(em.get("MAE"), em.get("RMSE"), kind="eggs")
        e4.metric("Eggs reliability", band)

        l1, l2, l3, l4 = st.columns(4)
        l1.metric("Location MAE", f"{lm['MAE']:.2f}" if lm.get("MAE") is not None else "—")
        l2.metric("Location RMSE", f"{lm['RMSE']:.2f}" if lm.get("RMSE") is not None else "—")
        exact = lm.get("Exact@code %")
        lband, lnote = _reliability_label(lm.get("MAE"), lm.get("RMSE"), kind="location", exact=exact)
        l3.metric("Exact code hit", f"{exact:.0f}%" if exact is not None else "—")
        l4.metric("Location reliability", lband)

        st.markdown(
            f"""
            <div class="insight-box">
                <strong>How to read this:</strong><br>
                • <strong>Eggs — {band}:</strong> {note}<br>
                • <strong>Location — {lband}:</strong> {lnote}<br>
                Lower MAE/RMSE is better. These scores use a hold-out slice of the monthly series
                (same style of check as your notebooks), so you can decide if the retrained models
                are solid enough for operational forecasts.
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">4. Saved model files</div>', unsafe_allow_html=True)
    rows = []
    for label, names in [("Eggs", EGGS_PKL_CANDIDATES), ("Location", LOC_PKL_CANDIDATES)]:
        for name in names:
            path = MODELS_DIR / name
            rows.append({
                "Model": label,
                "File": name,
                "Present": "Yes" if path.exists() else "No",
                "Size (KB)": round(path.stat().st_size / 1024, 1) if path.exists() else "—",
            })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Tip: copy your original `prophet_finaleggslaidmodel.pkl` and "
        "`prophet_model_location_last.pkl` into models/ so the app prefers them."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">Training series preview</div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["Eggs (monthly)", "Location L_TAGNUM (monthly)"])
    with t1:
        eggs_data = prepare_eggs_data(df)
        if eggs_data.empty:
            st.warning("Not enough data for the eggs series.")
        else:
            st.dataframe(eggs_data, use_container_width=True, height=280)
            st.caption(f"{len(eggs_data)} monthly points after feature engineering")
    with t2:
        loc_data = prepare_location_data(df)
        if loc_data.empty:
            st.warning("Not enough data for the location series.")
        else:
            st.dataframe(loc_data, use_container_width=True, height=280)
            st.caption(f"{len(loc_data)} monthly points after lag filter")
    st.markdown("</div>", unsafe_allow_html=True)
