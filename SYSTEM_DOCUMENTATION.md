# Turtle Analytical Insights — System Documentation

**Application type:** Streamlit analytical dashboard + Prophet forecasting  
**Domain:** Sea turtle nesting (La Union, Philippines)  
**Primary users:** Researchers, LGU / conservation staff, field coordinators  

---

## 1. Purpose

Turtle Analytical Insights provides:

1. **Descriptive analytics** on historical nesting records (counts, seasonality, barangay activity, hatching-related indicators).
2. **Predictive analytics** for:
   - Monthly average number of eggs laid
   - Most likely nesting location code (`L_TAGNUM` 0–11), mapped to barangay names
3. **Operational views** (map + Top 3 sites) and a controlled **retrain** path when new Excel data arrives.

The UI emphasizes plain-language callouts so non-technical stakeholders can interpret results.

---

## 2. Architecture

### 2.1 Runtime stack

| Layer | Technology |
|-------|------------|
| Presentation | Streamlit, custom CSS (`utils/theme.py`) |
| Charts | Plotly |
| Maps | Folium + streamlit-folium |
| Data | pandas, openpyxl |
| ML / forecast | Prophet (cmdstanpy backend), scikit-learn metrics |
| Persistence | Excel datasets; Prophet models as `.pkl` |

### 2.2 Module map

| Module | Responsibility |
|--------|----------------|
| `app.py` | Page config, theme injection, sidebar nav, shared dataset session state, route to views |
| `utils/data_loader.py` | Excel load, column aliases, date/numeric coercion, barangay maps, filters, monthly aggregation helper |
| `utils/models.py` | Feature prep, train, forecast, evaluate, load/save PKL, cache orchestration |
| `utils/theme.py` | Color tokens, global CSS, `chart_layout()` helper |
| `views/overview.py` | KPIs, filters, exploratory charts, data table |
| `views/eggs_forecast.py` | Eggs model UX |
| `views/location_forecast.py` | Location model UX |
| `views/nesting_map.py` | Geographic view + Top 3 KPIs |
| `views/model_mgmt.py` | Upload dataset, retrain, reliability metrics, PKL inventory |

### 2.3 Navigation design

- Custom **sidebar radio** only (labels: Overview, Eggs Forecast, Location Forecast, Nesting Map, Upload & Retrain).
- Page modules live under **`views/`**, not `pages/`, to avoid Streamlit multipage auto-discovery (which caused blank pages and path titles like `app/eggs_forecast`).
- Streamlit’s default sidebar page list is hidden via CSS.

### 2.4 Session state

| Key | Role |
|-----|------|
| `turtle_df` | Active pandas DataFrame |
| `data_source` | Label for auto path or uploaded filename |
| `retrain_ok` / `retrain_info` | Last retrain status and metrics |
| Forecast page keys | Horizon, year filters, last prediction results |

---

## 3. Data pipeline

### 3.1 Load sequence

1. On first run, `load_turtle_data()` searches known paths (including `data/FINALTURTLE_DATASET.xlsx`).
2. User may upload `.xlsx` / `.xls` from the sidebar or Upload & Retrain page.
3. Columns are normalized via alias map.
4. `DATE LAID` → datetime; key measures → numeric.
5. Derived fields: `YEAR`, `MONTH`, `MONTH_NAME`, `YEAR_MONTH`, `QUARTER`, `BARANGAY`, `BARANGAY_SHORT`.
6. Rows without a valid date are dropped.

### 3.2 Critical fields

- **Eggs path:** `DATE LAID`, `NO. OF EGGS LAID`
- **Location path:** `DATE LAID`, `L_TAGNUM` (0–11)

### 3.3 Barangay mapping

Integer `L_TAGNUM` maps to full barangay names and short labels used in filters, charts, and map popups. Approximate lat/lon pairs support map markers (visualization only; not survey-grade GPS).

---

## 4. Forecasting specification

### 4.1 Eggs Laid (notebook-aligned)

**Target:** monthly mean of `NO. OF EGGS LAID`.

**Features after aggregation:**

- Lags: `LAG_1`, `LAG_2`
- Smoothers: `EMA_3`, `EMA_5`
- Calendar flags: January, October, November, December

**Model:** Prophet additive; yearly + monthly + quarterly seasonality; listed columns as regressors.

**Forecast:** future frame with month flags; lag/EMA filled with last known values for future steps; uncertainty intervals from Prophet.

**Metrics (hold-out ~20%):** MAE, RMSE, MAPE.

### 4.2 Nesting location (original notebook process)

**Target:** monthly mean of `L_TAGNUM`.

**Preparation:**

1. Group by calendar month period; mean of `L_TAGNUM`.
2. Build `lag_1`, `lag_2`; drop rows with null lags.
3. Columns `ds`, `y` only are used for fitting.

**Model:**

```text
Prophet(
  yearly_seasonality=True,
  weekly_seasonality=False,
  daily_seasonality=False,
  seasonality_mode='additive'
)
+ quarterly seasonality (period=91.25, fourier_order=10)
```

**Prediction rule:**

1. `predict` on `ds` only  
2. `round(yhat)`  
3. Clip to integer range **[0, 11]**  
4. Map code → barangay name  

**Metrics (hold-out ~20%):** MAE and RMSE on rounded predictions vs actual monthly mean.  
Original notebook reference order of magnitude: MAE ≈ 0.59, RMSE ≈ 0.75, correlation ≈ 0.98.

**Retrain policy:** Reuse the same preparation and Prophet configuration so operational metrics remain comparable to the research notebook.

### 4.3 Model artifacts

| Artifact | Content |
|----------|---------|
| Eggs PKL | Fitted Prophet (eggs) |
| Location PKL | Fitted Prophet (location) — raw model object matching notebook save style |

Preferred filenames include original notebook names for drop-in compatibility.

---

## 5. UI / UX standards

### 5.1 Visual system

- Dark teal sidebar; light seafoam main background  
- KPI cards: fixed height for alignment across rows  
- Multiselect chips forced to sea teal (override Streamlit primary red)  
- Chart text/axis ticks: dark `#0A2647` on white plot area  

### 5.2 Readability for non-technical users

Each major page includes an **insight box** explaining what the view means in plain language (e.g. uncertainty band, top barangays, when to retrain).

---

## 6. Operational procedures

### 6.1 First deployment

1. Install Python 3.10+.  
2. Create and activate venv.  
3. `pip install -r requirements.txt`.  
4. Ensure dataset under `data/` or prepare upload.  
5. Optionally copy original PKLs into `models/`.  
6. `streamlit run app.py`.  

### 6.2 Seasonal data update

1. Clean new Excel to required schema.  
2. Upload & Retrain → upload file → **Retrain both models**.  
3. Confirm reliability bands and error metrics.  
4. Generate forecasts on Eggs / Location pages.  

### 6.3 Quality checks

- Column presence after upload  
- Non-empty monthly series after feature engineering  
- Hold-out metrics within expected ranges relative to historical notebook results  
- Map markers and Top 3 list consistent with filtered counts  

---

## 7. Limitations

- Location model predicts a **continuous average code**, not a full probability distribution over barangays; discrete site is obtained by rounding.  
- Map coordinates are approximate for visualization.  
- Forecast quality depends on data volume, coding consistency of `L_TAGNUM`, and stability of nesting behavior.  
- Prophet/Stan installation can be environment-specific on some Windows machines.  

---

## 8. File ownership summary

| Path | Owner concern |
|------|----------------|
| `app.py` | Routing, session dataset, theme bootstrap |
| `utils/data_loader.py` | Schema resilience and barangay reference data |
| `utils/models.py` | Must stay aligned with approved notebook methodology for location |
| `utils/theme.py` | Branding and accessibility of UI chrome |
| `views/*` | Page-level UX only; no alternate model math without design change |
| `models/*.pkl` | Generated or supplied artifacts; regenerate via retrain |
| `data/*.xlsx` | Authoritative nesting records |

---

## 9. Document control

| Item | Value |
|------|--------|
| Document | System Documentation |
| Product | Turtle Analytical Insights |
| Focus region | Bacnotan & San Juan, La Union, Philippines |
| Companion file | `README.md` (setup and user-oriented reference) |

For day-to-day setup and troubleshooting, use **README.md**.  
For architecture, data contracts, and model rules, use **this document**.
