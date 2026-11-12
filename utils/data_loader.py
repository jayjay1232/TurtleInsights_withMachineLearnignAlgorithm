"""
Data loading, cleaning helpers and barangay mapping for Turtle Analytical Insights
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Barangay mapping (L_TAGNUM → name)
BARANGAY_MAPPING = {
    0: "Baroro, Bacnotan, La Union",
    1: "Cabarsican, Bacnotan, La Union",
    2: "Galongen, Bacnotan, La Union",
    3: "Ili Norte, San Juan, La Union",
    4: "Ili Sur, San Juan, La Union",
    5: "Nagsimbaanan, Bacnotan, La Union",
    6: "Pandan, Bacnotan, La Union",
    7: "Panicsican, San Juan, La Union",
    8: "Población, Bacnotan, La Union",
    9: "Taboc, San Juan, La Union",
    10: "Tammocalao, Bacnotan, La Union",
    11: "Urbiztondo, San Juan, La Union",
}

# Approximate coastal coordinates (lat, lon) for map visualization
# Centered around Bacnotan / San Juan, La Union coastline
BARANGAY_COORDS = {
    0: (16.7092, 120.3419),   # Baroro
    1: (16.7250, 120.3480),   # Cabarsican (approx)
    2: (16.7561, 120.3391),   # Galongen
    3: (16.6700, 120.3350),   # Ili Norte, San Juan (approx)
    4: (16.6650, 120.3400),   # Ili Sur, San Juan (approx)
    5: (16.7400, 120.3450),   # Nagsimbaanan (approx)
    6: (16.7300, 120.3500),   # Pandan (approx)
    7: (16.6550, 120.3300),   # Panicsican, San Juan (approx)
    8: (16.7200, 120.3520),   # Población, Bacnotan
    9: (16.6800, 120.3380),   # Taboc, San Juan (approx)
    10: (16.7150, 120.3550),  # Tammocalao (approx)
    11: (16.6900, 120.3450),  # Urbiztondo, San Juan (approx)
}

SHORT_NAMES = {
    0: "Baroro",
    1: "Cabarsican",
    2: "Galongen",
    3: "Ili Norte",
    4: "Ili Sur",
    5: "Nagsimbaanan",
    6: "Pandan",
    7: "Panicsican",
    8: "Población",
    9: "Taboc",
    10: "Tammocalao",
    11: "Urbiztondo",
}

# Possible column name variants (user dataset may have slight differences)
COLUMN_ALIASES = {
    "TURTLE_NUM": ["TURTLE_NUM", "TURTLE NUM", "Turtle_Num", "turtle_num", "ID"],
    "DATE LAID": ["DATE LAID", "DATE_LAID", "Date Laid", "date_laid", "DATE"],
    "NO. OF EGGS LAID": ["NO. OF EGGS LAID", "NO OF EGGS LAID", "EGGS_LAID", "Eggs Laid", "eggs_laid", "NO. EGGS"],
    "NO. OF HATCHLING RELEASED": ["NO. OF HATCHLING RELEASED", "HATCHLINGS", "HATCHLING RELEASED", "hatchlings"],
    "UNHATCHED EGGS": ["UNHATCHED EGGS", "UNHATCHED", "unhatched"],
    "HATCHING RATE": ["HATCHING RATE", "HATCH_RATE", "hatching_rate"],
    "LOCATION": ["LOCATION", "Location", "location"],
    "L_TAGNUM": [
        "L_TAGNUM", "L TAGNUM", "L_TAG", "L-TAGNUM", "location_code", "TAGNUM",
        "LOCATION_CODE", "LOC_CODE", "BARANGAY_CODE", "SITE_CODE", "SITE",
    ],
}

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to canonical names using aliases."""
    rename_map = {}
    lower_cols = {c.lower().strip(): c for c in df.columns}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in lower_cols:
                rename_map[lower_cols[alias.lower()]] = canonical
                break
    return df.rename(columns=rename_map)

def load_turtle_data(file_or_path=None) -> pd.DataFrame:
    """
    Load and lightly prepare the turtle nesting dataset.
    Accepts a path, uploaded file, or looks in common locations.
    """
    df = None

    if file_or_path is not None:
        if hasattr(file_or_path, "read"):
            df = pd.read_excel(file_or_path)
        else:
            df = pd.read_excel(file_or_path)
    else:
        # Search common locations relative to this project
        search_paths = [
            Path(__file__).parent.parent / "data" / "FINALTURTLE_DATASET.xlsx",
            Path(__file__).parent.parent / "data" / "FINALMODE_DATASET.xlsx",
            Path(__file__).parent.parent / "FINALTURTLE_DATASET.xlsx",
            Path.cwd() / "FINALTURTLE_DATASET.xlsx",
            Path.cwd() / "data" / "FINALTURTLE_DATASET.xlsx",
        ]
        for p in search_paths:
            if p.exists():
                df = pd.read_excel(p)
                break

    if df is None:
        return None

    df = _normalize_columns(df)

    # Parse date
    if "DATE LAID" in df.columns:
        df["DATE LAID"] = pd.to_datetime(df["DATE LAID"], errors="coerce")

    # Ensure numeric fields
    for col in ["NO. OF EGGS LAID", "NO. OF HATCHLING RELEASED", "UNHATCHED EGGS",
                "HATCHING RATE", "L_TAGNUM", "TURTLE_NUM"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derived helpers
    if "DATE LAID" in df.columns:
        df["YEAR"] = df["DATE LAID"].dt.year
        df["MONTH"] = df["DATE LAID"].dt.month
        df["MONTH_NAME"] = df["DATE LAID"].dt.strftime("%B")
        df["YEAR_MONTH"] = df["DATE LAID"].dt.to_period("M").astype(str)
        df["QUARTER"] = df["DATE LAID"].dt.quarter

    # Map barangay name
    if "L_TAGNUM" in df.columns:
        # coerce codes that may be floats/strings
        df["L_TAGNUM"] = pd.to_numeric(df["L_TAGNUM"], errors="coerce")
        df["BARANGAY"] = df["L_TAGNUM"].map(BARANGAY_MAPPING)
        df["BARANGAY_SHORT"] = df["L_TAGNUM"].map(SHORT_NAMES)
    elif "LOCATION" in df.columns:
        # Best-effort: extract trailing number from values like "Site-10" / "Site 3"
        extracted = (
            df["LOCATION"].astype(str)
            .str.extract(r"(\d+)", expand=False)
        )
        codes = pd.to_numeric(extracted, errors="coerce")
        if codes.notna().any():
            df["L_TAGNUM"] = codes
            df["BARANGAY"] = df["L_TAGNUM"].map(BARANGAY_MAPPING)
            df["BARANGAY_SHORT"] = df["L_TAGNUM"].map(SHORT_NAMES)

    # Drop rows with no date (critical for time series)
    if "DATE LAID" in df.columns:
        df = df.dropna(subset=["DATE LAID"]).copy()

    return df

def get_filter_options(df: pd.DataFrame) -> dict:
    """Return available filter values from the dataframe."""
    opts = {}
    if "YEAR" in df.columns:
        opts["years"] = sorted(df["YEAR"].dropna().unique().astype(int).tolist())
    if "MONTH" in df.columns:
        opts["months"] = sorted(df["MONTH"].dropna().unique().astype(int).tolist())
    if "L_TAGNUM" in df.columns:
        opts["locations"] = sorted(df["L_TAGNUM"].dropna().unique().astype(int).tolist())
    if "QUARTER" in df.columns:
        opts["quarters"] = sorted(df["QUARTER"].dropna().unique().astype(int).tolist())
    return opts

def apply_filters(df: pd.DataFrame, years=None, months=None, locations=None, quarters=None) -> pd.DataFrame:
    """Apply selected filters and return filtered dataframe."""
    filtered = df.copy()
    if years and "YEAR" in filtered.columns:
        filtered = filtered[filtered["YEAR"].isin(years)]
    if months and "MONTH" in filtered.columns:
        filtered = filtered[filtered["MONTH"].isin(months)]
    if locations is not None and len(locations) > 0 and "L_TAGNUM" in filtered.columns:
        filtered = filtered[filtered["L_TAGNUM"].isin(locations)]
    if quarters and "QUARTER" in filtered.columns:
        filtered = filtered[filtered["QUARTER"].isin(quarters)]
    return filtered

def monthly_agg(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Aggregate to monthly mean for a numeric column."""
    if "DATE LAID" not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    tmp = df.dropna(subset=["DATE LAID", value_col]).copy()
    tmp["NESTING_YEAR_MONTH"] = tmp["DATE LAID"].dt.to_period("M")
    monthly = tmp.groupby("NESTING_YEAR_MONTH")[value_col].mean().reset_index()
    monthly["ds"] = monthly["NESTING_YEAR_MONTH"].dt.to_timestamp()
    monthly = monthly.rename(columns={value_col: "y"})
    return monthly[["ds", "y"]].sort_values("ds").reset_index(drop=True)
