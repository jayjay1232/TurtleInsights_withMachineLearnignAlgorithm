# 🐢 Turtle Analytical Insights

**Sea turtle nesting analytics & Prophet forecasting for La Union, Philippines**

Turtle Analytical Insights is a Streamlit dashboard for exploring historical nesting activity and generating forecasts for:

- **Monthly average eggs laid**
- **Most likely nesting barangay (location)**

It is designed for researchers, LGU staff, and field teams who need clear KPIs, maps, and forecasts without reading technical notebooks.

---

## Table of Contents

1. [Features](#1-features)
2. [System Overview](#2-system-overview)
3. [Project Structure](#3-project-structure)
4. [Requirements](#4-requirements)
5. [Installation & Setup](#5-installation--setup)
6. [How to Run](#6-how-to-run)
7. [Dataset Specification](#7-dataset-specification)
8. [Application Pages](#8-application-pages)
9. [Predictive Models](#9-predictive-models)
10. [Model Files (PKL)](#10-model-files-pkl)
11. [Upload & Retrain Workflow](#11-upload--retrain-workflow)
12. [Theme & UI Notes](#12-theme--ui-notes)
13. [Troubleshooting](#13-troubleshooting)
14. [Glossary](#14-glossary)

---

## 1. Features

| Area | Capability |
|------|------------|
| **Overview** | KPI cards, monthly activity, barangay ranking, eggs over time, yearly comparison, distributions, heatmap, data table |
| **Eggs Forecast** | Prophet time-series forecast of monthly average eggs; target year selection; hold-out MAE / RMSE / MAPE |
| **Location Forecast** | Prophet forecast of monthly average `L_TAGNUM` → rounded barangay code; multi-month outlook; nearest alternative sites |
| **Nesting Map** | Interactive Folium map of Bacnotan & San Juan sites; filters; Top 3 nesting barangays |
| **Upload & Retrain** | Load new Excel data and retrain both models; reliability metrics after retrain |
| **UI** | Single sidebar navigation (no cluttered multipage titles); sea-themed styling; plain-language insight boxes |

---

## 2. System Overview

```
┌─────────────────────┐
│   Streamlit (app.py)│
│   Sidebar navigation│
└──────────┬──────────┘
           │
     ┌─────┴──────────────────────────────┐
     │            views/                  │
     │  overview · eggs · location        │
     │  map · upload & retrain            │
     └─────┬──────────────────────────────┘
           │
   ┌───────┴────────┐      ┌──────────────┐
   │ utils/         │      │ data/        │
   │ data_loader.py │◄────►│ *.xlsx       │
   │ models.py      │      └──────────────┘
   │ theme.py       │
   └───────┬────────┘
           │
   ┌───────▼────────┐
   │ models/        │
   │ *.pkl (Prophet)│
   └────────────────┘
```

- **Entry point:** `app.py`
- **Pages:** modules under `views/` (not Streamlit’s auto `pages/` folder)
- **Data:** Excel in `data/` or uploaded in the sidebar / Upload & Retrain page
- **Models:** Facebook Prophet, saved as pickle files under `models/`

---

## 3. Project Structure

```
Turtle_Analytical_Insights/
│
├── app.py                 # Main Streamlit entry point & navigation
├── requirements.txt       # Python dependencies
├── README.md              # This documentation
│
├── data/
│   ├── FINALTURTLE_DATASET.xlsx   # Default nesting dataset
│   └── generate_sample.py         # Optional sample generator
│
├── models/
│   ├── prophet_eggs_laid.pkl              # Eggs model (project name)
│   ├── prophet_finaleggslaidmodel.pkl     # Eggs model (notebook name, optional)
│   ├── prophet_location.pkl               # Location model (project name)
│   └── prophet_model_location_last.pkl    # Location model (notebook name, optional)
│
├── utils/
│   ├── __init__.py
│   ├── data_loader.py     # Load, clean, map barangays, filters
│   ├── models.py          # Prepare / train / forecast / evaluate Prophet models
│   └── theme.py           # Colors, CSS theme, chart layout helpers
│
└── views/
    ├── __init__.py
    ├── overview.py        # Overview & Insights
    ├── eggs_forecast.py   # Eggs Laid Forecast
    ├── location_forecast.py
    ├── nesting_map.py
    └── model_mgmt.py      # Upload & Retrain
```

> **Important:** Do **not** put page modules in a folder named `pages/`. Streamlit auto-loads that folder as multipage routes and will show blank pages. This app uses **`views/`** and a custom sidebar radio.

---

## 4. Requirements

| Package | Purpose |
|---------|---------|
| streamlit | Web UI |
| pandas, numpy | Data handling |
| prophet, cmdstanpy | Time-series forecasting |
| plotly | Interactive charts |
| folium, streamlit-folium | Map page |
| scikit-learn | MAE / RMSE metrics |
| openpyxl, xlsxwriter | Excel read/write |
| matplotlib, seaborn | Optional plotting support |
| Pillow | Image support |

Python **3.10+** recommended (3.11 tested).

---

## 5. Installation & Setup

### Windows (PowerShell)

```powershell
# 1. Open the folder that contains app.py
cd "C:\xamppp\htdocs\Python Dashboard Practice\Turtle_Analytical_Insights"

# 2. Create virtual environment
python -m venv venv
# or:  py -m venv venv

# 3. Activate
.\venv\Scripts\Activate.ps1
# If blocked:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# Or use:  .\venv\Scripts\activate.bat

# 4. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux

```bash
cd Turtle_Analytical_Insights
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Optional: original notebook PKL files

Copy your trained models into `models/`:

| Notebook output | Place as |
|-----------------|----------|
| `prophet_finaleggslaidmodel.pkl` | `models/prophet_finaleggslaidmodel.pkl` |
| `prophet_model_location_last.pkl` | `models/prophet_model_location_last.pkl` |

The app prefers these names when present; otherwise it uses project names or trains from data.

---

## 6. How to Run

```powershell
# venv activated, inside project root
streamlit run app.py
```

Browser opens at `http://localhost:8501` (default).

Use the **left sidebar** to switch pages. Dataset status appears under **Dataset** in the sidebar.

---

## 7. Dataset Specification

### Expected columns

| Column | Required | Description |
|--------|----------|-------------|
| `DATE LAID` | Yes | Nesting date |
| `NO. OF EGGS LAID` | Yes (eggs model) | Eggs per nest (numeric) |
| `L_TAGNUM` | Yes (location model) | Location code **0–11** |
| `NO. OF HATCHLING RELEASED` | Optional | For hatching KPIs |
| `UNHATCHED EGGS` | Optional | |
| `HATCHING RATE` | Optional | 0–1 or 0–100 |
| `LOCATION` | Optional | Text site label |
| `TURTLE_NUM` | Optional | Nest / turtle ID |

Column name variants are normalized automatically (e.g. `DATE_LAID`, `Eggs Laid`, `L TAGNUM`).

### Location codes (`L_TAGNUM`)

| Code | Barangay |
|------|----------|
| 0 | Baroro, Bacnotan, La Union |
| 1 | Cabarsican, Bacnotan, La Union |
| 2 | Galongen, Bacnotan, La Union |
| 3 | Ili Norte, San Juan, La Union |
| 4 | Ili Sur, San Juan, La Union |
| 5 | Nagsimbaanan, Bacnotan, La Union |
| 6 | Pandan, Bacnotan, La Union |
| 7 | Panicsican, San Juan, La Union |
| 8 | Población, Bacnotan, La Union |
| 9 | Taboc, San Juan, La Union |
| 10 | Tammocalao, Bacnotan, La Union |
| 11 | Urbiztondo, San Juan, La Union |

Default file path searched on startup:

- `data/FINALTURTLE_DATASET.xlsx`

---

## 8. Application Pages

### Overview

- KPI cards: nests, eggs, average eggs/nest, hatching rate or hatchlings, active locations
- Filters: year, month, barangay
- Charts: monthly activity, nests by barangay, eggs over time, yearly comparison
- Tabs: distribution, hatching performance, seasonality heatmap, data table
- Plain-language insight box for non-technical users

### Eggs Forecast

- Prophet model of **monthly average eggs laid**
- Controls: target year (from 2015 onward), extra months, force retrain
- Chart: historical series + forecast + uncertainty band
- Table: predicted averages by month/year
- Metrics: training months, hold-out MAE, RMSE, MAPE

### Location Forecast

- Prophet model of **monthly average `L_TAGNUM`**
- Multi-month outlook (default 12 months)
- Primary barangay = rounded and clipped prediction (0–11)
- Optional nearest alternative barangays (by distance to predicted score)
- Metrics: MAE, RMSE (aligned with original notebook evaluation)

### Nesting Map

- Folium map of coastal barangays
- Filters: year, month, map style (markers / heatmap / both)
- KPI row: locations with nests, total nests, total eggs, **Top 3 nesting barangays**

### Upload and Retrain

1. Upload a new Excel file
2. Review dataset snapshot
3. **Retrain both models**
4. Review hold-out reliability metrics (eggs + location)
5. Inspect saved PKL files and training series previews

---

## 9. Predictive Models

Models follow the original research notebooks.

### Eggs Laid model

1. Aggregate to **monthly mean** of `NO. OF EGGS LAID`
2. Features: `LAG_1`, `LAG_2`, `EMA_3`, `EMA_5`, January / October / November / December flags
3. Prophet: yearly + monthly + quarterly seasonality; regressors as above
4. Forecast horizon: configurable (extends through selected target year)

### Location model (original notebook process)

1. Aggregate to **monthly mean** of `L_TAGNUM`
2. Create `lag_1` / `lag_2` and drop early rows with missing lags
3. **Important:** lags are used only to filter the series — they are **not** added as Prophet regressors
4. Rename columns to `ds` / `y`
5. Prophet: yearly seasonality + quarterly seasonality (`period=91.25`, `fourier_order=10`)
6. Fit on `ds` and `y` only
7. Predict with `ds` only → **round** `yhat` → **clip to 0–11** → map to barangay name

**Reference hold-out quality (original notebook on FINALMODE dataset):**

| Metric | Approx. value |
|--------|----------------|
| MAE | ~0.59 |
| RMSE | ~0.75 |
| Correlation | ~0.98 |

Retrain should use the **same preparation and Prophet setup** so metrics stay aligned with the notebook when the data are comparable.

### Evaluation

- Hold-out = last ~20% of the monthly series
- Eggs: MAE, RMSE, MAPE
- Location: MAE, RMSE on rounded predictions vs actual monthly mean

---

## 10. Model Files (PKL)

| File | Model |
|------|--------|
| `prophet_eggs_laid.pkl` / `prophet_finaleggslaidmodel.pkl` | Eggs |
| `prophet_location.pkl` / `prophet_model_location_last.pkl` | Location |

Load order prefers **notebook filenames**, then project filenames. If missing or unloadable, the app trains from the current dataset and saves both naming styles where applicable.

---

## 11. Upload and Retrain Workflow

1. Place new cleaned Excel in the uploader (sidebar or Upload & Retrain page).
2. Confirm required columns are present.
3. Click **Retrain both models**.
4. Read reliability labels:
   - **Strong** — low error vs scale of the target
   - **Acceptable** — usable for planning with caution
   - **Weak** — collect more data or check data quality
5. Return to Eggs / Location pages to generate forecasts with the refreshed models.

---

## 12. Theme and UI Notes

| Item | Location |
|------|----------|
| Color palette | `utils/theme.py` → `COLORS` |
| Global CSS (sidebar, cards, filters) | `utils/theme.py` → `CUSTOM_CSS` |
| Chart axis readability helper | `utils/theme.py` → `chart_layout()` |
| Filter chip color (teal, not red) | Theme CSS + runtime override in `app.py` |

**Brand colors (examples):**

- Deep ocean `#0A2647`
- Sea teal `#0D7377`
- Bright sea `#14919B`
- Seafoam `#E8F6F3`

In f-strings, CSS braces must be written as `{{` and `}}`.

---

## 13. Troubleshooting

| Problem | What to do |
|---------|------------|
| `venv\Scripts\activate` not found | Create venv first: `python -m venv venv` from the folder that contains `app.py` |
| Blank pages / titles like `app/eggs_forecast` | Delete any `pages/` folder; use only `views/` and sidebar radio |
| `SyntaxError` in `theme.py` around `#0D7377` | CSS `{` `}` inside an f-string must be doubled (`{{` `}}`) |
| `Regressor 'lag_1' missing` | Location model must match notebook: **no lag regressors** on Prophet; retrain after restoring original location training code |
| Red year/month chips | Hard refresh (`Ctrl+F5`); ensure latest `theme.py` and `app.py` |
| Unreadable chart axis text | Charts should use dark `#0A2647` fonts via layout helpers |
| Prophet / cmdstanpy install issues | Use a clean venv; on Windows install build tools if Stan backend fails |
| Dataset not loading | Check path `data/FINALTURTLE_DATASET.xlsx` or upload via sidebar |

---

## 14. Glossary

| Term | Meaning |
|------|---------|
| **Nest** | One recorded nesting event |
| **Eggs laid** | Count of eggs in a nest |
| **Hatching rate** | Share of eggs that produced hatchlings (dataset-dependent scale) |
| **L_TAGNUM** | Integer code (0–11) for nesting barangay |
| **Prophet** | Facebook/Meta open-source time-series forecasting library |
| **Hold-out** | Last portion of the monthly series used to compute error metrics |
| **MAE / RMSE / MAPE** | Mean absolute error, root mean squared error, mean absolute percentage error |

---

## Quick Start Checklist

- [ ] Python 3.10+ installed
- [ ] Project extracted; working directory contains `app.py`
- [ ] `python -m venv venv` and venv activated
- [ ] `pip install -r requirements.txt`
- [ ] Dataset in `data/FINALTURTLE_DATASET.xlsx` (or upload in UI)
- [ ] Optional: original `.pkl` files copied into `models/`
- [ ] `streamlit run app.py`
- [ ] Sidebar navigation works; no leftover `pages/` folder

---

**Turtle Analytical Insights** · La Union coastal nesting sites · Analytical dashboard and Prophet forecasting
