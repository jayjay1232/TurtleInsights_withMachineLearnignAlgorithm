
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

from utils.data_loader import BARANGAY_MAPPING

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Preferred pickle names (original notebook names first, then project defaults)
EGGS_PKL_CANDIDATES = [
    "prophet_finaleggslaidmodel.pkl",
    "prophet_eggs_laid.pkl",
]
LOC_PKL_CANDIDATES = [
    "prophet_model_location_last.pkl",
    "prophet_location.pkl",
]


def _safe_mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def _find_pkl(candidates):
    for name in candidates:
        path = MODELS_DIR / name
        if path.exists():
            return path
    return MODELS_DIR / candidates[-1]


def _load_pkl(path: Path):
    if not path.exists():
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Eggs Laid 
# ---------------------------------------------------------------------------

def prepare_eggs_data(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly average eggs + lag / EMA / month indicators (original notebook)."""
    if df is None or df.empty:
        return pd.DataFrame()
    if "DATE LAID" not in df.columns or "NO. OF EGGS LAID" not in df.columns:
        return pd.DataFrame()

    tmp = df.dropna(subset=["DATE LAID", "NO. OF EGGS LAID"]).copy()
    tmp["NESTING_YEAR_MONTH"] = tmp["DATE LAID"].dt.to_period("M")
    monthly = tmp.groupby("NESTING_YEAR_MONTH")["NO. OF EGGS LAID"].mean().reset_index()
    monthly["ds"] = monthly["NESTING_YEAR_MONTH"].dt.to_timestamp()
    monthly = monthly.rename(columns={"NO. OF EGGS LAID": "y"})
    prophet_data = monthly[["ds", "y"]].sort_values("ds").reset_index(drop=True)

    prophet_data["LAG_1"] = prophet_data["y"].shift(1)
    prophet_data["LAG_2"] = prophet_data["y"].shift(2)
    prophet_data["EMA_3"] = prophet_data["y"].ewm(span=3, adjust=False).mean()
    prophet_data["EMA_5"] = prophet_data["y"].ewm(span=5, adjust=False).mean()
    prophet_data["JANUARY"] = (prophet_data["ds"].dt.month == 1).astype(int)
    prophet_data["OCTOBER"] = (prophet_data["ds"].dt.month == 10).astype(int)
    prophet_data["NOVEMBER"] = (prophet_data["ds"].dt.month == 11).astype(int)
    prophet_data["DECEMBER"] = (prophet_data["ds"].dt.month == 12).astype(int)
    prophet_data = prophet_data.dropna().reset_index(drop=True)
    return prophet_data


def train_eggs_model(prophet_data: pd.DataFrame, save: bool = True):
    """Train eggs model exactly as in the original notebook."""
    if prophet_data is None or prophet_data.empty:
        return None

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="additive",
    )
    model.add_seasonality(name="monthly", period=12, fourier_order=5)
    model.add_seasonality(name="quarterly", period=3, fourier_order=3)

    for reg in ["LAG_1", "LAG_2", "EMA_3", "EMA_5", "JANUARY", "OCTOBER", "NOVEMBER", "DECEMBER"]:
        if reg in prophet_data.columns:
            model.add_regressor(reg)

    model.fit(prophet_data)

    if save:
        for name in ("prophet_eggs_laid.pkl", "prophet_finaleggslaidmodel.pkl"):
            with open(MODELS_DIR / name, "wb") as f:
                pickle.dump(model, f)
    return model


def forecast_eggs(model, prophet_data: pd.DataFrame, periods: int = 12):
    """12-month (or custom) forecast with regressor handling."""
    if model is None or prophet_data is None or prophet_data.empty:
        return pd.DataFrame()

    future = model.make_future_dataframe(periods=periods, freq="MS")
    last_y = float(prophet_data["y"].iloc[-1])
    last_ema3 = float(prophet_data["EMA_3"].iloc[-1]) if "EMA_3" in prophet_data.columns else last_y
    last_ema5 = float(prophet_data["EMA_5"].iloc[-1]) if "EMA_5" in prophet_data.columns else last_y
    hist_len = len(prophet_data)

    for col, fill in [
        ("LAG_1", last_y),
        ("LAG_2", last_y),
        ("EMA_3", last_ema3),
        ("EMA_5", last_ema5),
    ]:
        future[col] = np.nan
        if col in prophet_data.columns:
            future.loc[: hist_len - 1, col] = prophet_data[col].values
        future.loc[hist_len:, col] = fill

    future["JANUARY"] = (future["ds"].dt.month == 1).astype(int)
    future["OCTOBER"] = (future["ds"].dt.month == 10).astype(int)
    future["NOVEMBER"] = (future["ds"].dt.month == 11).astype(int)
    future["DECEMBER"] = (future["ds"].dt.month == 12).astype(int)
    future = future.ffill().bfill()
    return model.predict(future)


def evaluate_eggs_model(model, prophet_data: pd.DataFrame, test_ratio: float = 0.2):
    if model is None or prophet_data is None or len(prophet_data) < 8:
        return {}, pd.DataFrame()
    train_size = int(len(prophet_data) * (1 - test_ratio))
    test = prophet_data.iloc[train_size:].copy()
    if test.empty:
        return {}, pd.DataFrame()
    cols = ["ds"] + [
        c
        for c in ["LAG_1", "LAG_2", "EMA_3", "EMA_5", "JANUARY", "OCTOBER", "NOVEMBER", "DECEMBER"]
        if c in test.columns
    ]
    pred = model.predict(test[cols])
    merged = pred[["ds", "yhat"]].merge(test[["ds", "y"]], on="ds", how="right")
    metrics = {
        "MAE": float(mean_absolute_error(merged["y"], merged["yhat"])),
        "RMSE": float(np.sqrt(mean_squared_error(merged["y"], merged["yhat"]))),
        "MAPE": _safe_mape(merged["y"], merged["yhat"]),
    }
    return metrics, merged


# ---------------------------------------------------------------------------
# Location 
# ---------------------------------------------------------------------------

def prepare_location_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exact original notebook preparation:
    - monthly mean of L_TAGNUM
    - lag_1 / lag_2 (kept for compatibility / inspection, NOT used as regressors)
    """
    if df is None or df.empty:
        return pd.DataFrame()
    if "DATE LAID" not in df.columns or "L_TAGNUM" not in df.columns:
        return pd.DataFrame()

    tmp = df.dropna(subset=["DATE LAID", "L_TAGNUM"]).copy()
    tmp["NESTING_YEAR_MONTH"] = tmp["DATE LAID"].dt.to_period("M")

    monthly = (
        tmp.groupby("NESTING_YEAR_MONTH")["L_TAGNUM"]
        .mean()
        .reset_index()
        .rename(columns={"L_TAGNUM": "y"})
    )
    monthly["ds"] = monthly["NESTING_YEAR_MONTH"].dt.to_timestamp()
    monthly = monthly.sort_values("ds").reset_index(drop=True)

    # lags are computed exactly as in the notebook (but never added as regressors)
    monthly["lag_1"] = monthly["y"].shift(1)
    monthly["lag_2"] = monthly["y"].shift(2)
    monthly = monthly.dropna(subset=["lag_1", "lag_2"]).reset_index(drop=True)

    return monthly


def train_location_model(prophet_data: pd.DataFrame, save: bool = True):
    """
    Exact original notebook model:
    - yearly_seasonality=True
    - quarterly seasonality (period=91.25, fourier_order=10)
    - NO extra regressors
    """
    if prophet_data is None or prophet_data.empty:
        return None

    # Only ds + y are used (lags stay in the frame but are ignored by Prophet)
    fit_df = prophet_data[["ds", "y"]].copy()

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="additive",
    )
    model.add_seasonality(name="quarterly", period=91.25, fourier_order=10)

    model.fit(fit_df)

    if save:
        # Save raw Prophet object (matches original notebook pickle)
        for name in ("prophet_model_location_last.pkl", "prophet_location.pkl"):
            with open(MODELS_DIR / name, "wb") as f:
                pickle.dump(model, f)
    return model


def _unwrap_location_model(model):
    """
    Support both:
    - raw Prophet (original notebook)
    - legacy {model, regressors} dicts from earlier experiments
    """
    if model is None:
        return None, []
    if isinstance(model, dict) and "model" in model:
        m = model["model"]
        regs = list(model.get("regressors") or [])
        if not regs and hasattr(m, "extra_regressors") and m.extra_regressors:
            regs = list(m.extra_regressors.keys())
        return m, regs
    # raw Prophet
    regs = []
    if hasattr(model, "extra_regressors") and model.extra_regressors:
        regs = list(model.extra_regressors.keys())
    return model, regs


def forecast_location(
    model,
    periods: int = 12,
    start_date=None,
    prophet_data: pd.DataFrame | None = None,  # kept for API compatibility
):
    """Multi-step forecast. Original model needs only the date column."""
    model, _ = _unwrap_location_model(model)
    if model is None:
        return pd.DataFrame()

    if start_date is None:
        future = model.make_future_dataframe(periods=periods, freq="MS")
    else:
        future = pd.DataFrame({"ds": pd.date_range(start=start_date, periods=periods, freq="MS")})

    forecast = model.predict(future)
    forecast["predicted_l_tagnum"] = forecast["yhat"].round().clip(0, 11).astype(int)
    forecast["barangay"] = forecast["predicted_l_tagnum"].map(BARANGAY_MAPPING)
    return forecast


def predict_location_for_date(
    model,
    year: int,
    month: int,
    prophet_data: pd.DataFrame | None = None,  # kept for API compatibility
) -> dict:
    """Single-month barangay prediction – exact original notebook API."""
    model, _ = _unwrap_location_model(model)
    if model is None:
        return {
            "Date": None,
            "Predicted Barangay": "Model not available",
            "L_TAGNUM": None,
            "yhat": None,
        }

    input_date = pd.to_datetime(f"{year}-{month:02d}-01")
    future_df = pd.DataFrame({"ds": [input_date]})
    forecast = model.predict(future_df)

    pred = int(round(float(forecast["yhat"].iloc[0])))
    pred = max(0, min(pred, 11))

    return {
        "Date": input_date,
        "Predicted Barangay": BARANGAY_MAPPING.get(pred, "Unknown Location"),
        "L_TAGNUM": pred,
        "yhat": float(forecast["yhat"].iloc[0]),
    }


def evaluate_location_model(model, prophet_data: pd.DataFrame, test_ratio: float = 0.2):
    """
    Evaluation exactly as in the original notebook:
    - last 20 % hold-out
    - round(yhat) vs continuous mean y
    - MAE / RMSE
    """
    model, _ = _unwrap_location_model(model)
    if model is None or prophet_data is None or len(prophet_data) < 6:
        return {}, pd.DataFrame()

    train_size = int(len(prophet_data) * (1 - test_ratio))
    test = prophet_data.iloc[train_size:].copy()
    if test.empty:
        return {}, pd.DataFrame()

    pred = model.predict(test[["ds"]])
    merged = pred[["ds", "yhat"]].merge(test[["ds", "y"]], on="ds", how="right")
    merged["yhat_rounded"] = merged["yhat"].round().clip(0, 11)

    metrics = {
        "MAE": float(mean_absolute_error(merged["y"], merged["yhat_rounded"])),
        "RMSE": float(np.sqrt(mean_squared_error(merged["y"], merged["yhat_rounded"]))),
        "Exact@code %": float((merged["yhat_rounded"] == merged["y"].round()).mean() * 100),
    }
    return metrics, merged


# ---------------------------------------------------------------------------
# Caching / force retrain
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_or_train_models(df: pd.DataFrame, force_retrain: bool = False):
    """Prefer original PKL files; train only if missing or force_retrain."""
    eggs_data = prepare_eggs_data(df) if df is not None else pd.DataFrame()
    loc_data = prepare_location_data(df) if df is not None else pd.DataFrame()

    eggs_path = _find_pkl(EGGS_PKL_CANDIDATES)
    loc_path = _find_pkl(LOC_PKL_CANDIDATES)

    eggs_model = None if force_retrain else _load_pkl(eggs_path)
    loc_model = None if force_retrain else _load_pkl(loc_path)

    if eggs_model is None and not eggs_data.empty:
        eggs_model = train_eggs_model(eggs_data, save=True)
    if loc_model is None and not loc_data.empty:
        loc_model = train_location_model(loc_data, save=True)

    return eggs_model, loc_model, eggs_data, loc_data


def retrain_all(df: pd.DataFrame):
    """Force retrain both models from the given dataframe and refresh cache."""
    eggs_data = prepare_eggs_data(df)
    loc_data = prepare_location_data(df)
    eggs_model = train_eggs_model(eggs_data, save=True) if not eggs_data.empty else None
    loc_model = train_location_model(loc_data, save=True) if not loc_data.empty else None
    try:
        get_or_train_models.clear()
    except Exception:
        pass
    return eggs_model, loc_model, eggs_data, loc_data