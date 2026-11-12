"""
Turtle Analytical Insights
Main entry point – single-file navigation (no Streamlit multipage chrome)
"""

import streamlit as st
from pathlib import Path
import sys

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.theme import inject_theme
from utils.data_loader import load_turtle_data

st.set_page_config(
    page_title="Turtle Analytical Insights",
    page_icon="🐢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Turtle Analytical Insights – Sea turtle nesting analytics for La Union, Philippines"
    },
)

inject_theme()
# Runtime override: Streamlit primary (red) chips → teal
st.markdown(
    """
    <style>
    [data-baseweb="tag"], span[data-baseweb="tag"], div[data-baseweb="tag"] {
        background-color: #0D7377 !important;
        background-image: none !important;
        color: #fff !important;
        border: 0 !important;
    }
    [data-baseweb="tag"] span { color: #fff !important; }
    [data-baseweb="tag"] svg { fill: #fff !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

NAV = [
    ("overview", "🏠  Overview"),
    ("eggs", "🥚  Eggs Forecast"),
    ("location", "📍  Location Forecast"),
    ("map", "🗺️  Nesting Map"),
    ("retrain", "📂  Upload & Retrain"),
]

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 0.4rem 0 1rem 0;">
            <div style="font-size:2.5rem;">🐢</div>
            <div style="font-size:1.05rem; font-weight:700; color:#E8F6F3; letter-spacing:0.3px;">
                Turtle Analytical Insights
            </div>
            <div style="font-size:0.75rem; color:#A5D8D6; margin-top:3px;">
                La Union Nesting Analytics
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    labels = [label for _, label in NAV]
    choice = st.radio("Navigate", labels, label_visibility="collapsed", key="main_nav")
    # map selected label to page key
    # map label back to key
    page_key = {lab: k for k, lab in NAV}[choice]

    st.markdown("---")
    st.markdown("#### 📂 Dataset")
    uploaded = st.file_uploader(
        "Upload Excel (.xlsx)",
        type=["xlsx", "xls"],
        help="Upload FINALTURTLE_DATASET.xlsx or a compatible cleaned file",
        label_visibility="collapsed",
        key="sidebar_upload",
    )

if "turtle_df" not in st.session_state:
    st.session_state.turtle_df = None
    st.session_state.data_source = None

if st.session_state.turtle_df is None:
    auto = load_turtle_data()
    if auto is not None and not auto.empty:
        st.session_state.turtle_df = auto
        st.session_state.data_source = "auto (data folder)"

if uploaded is not None:
    try:
        df_up = load_turtle_data(uploaded)
        if df_up is not None and not df_up.empty:
            st.session_state.turtle_df = df_up
            st.session_state.data_source = uploaded.name
            try:
                from utils.models import get_or_train_models
                get_or_train_models.clear()
            except Exception:
                pass
            st.sidebar.success(f"Loaded {len(df_up):,} records")
        else:
            st.sidebar.error("Could not parse the uploaded file.")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")

with st.sidebar:
    if st.session_state.turtle_df is not None:
        st.caption(
            f"✅ {len(st.session_state.turtle_df):,} nests  •  "
            f"{st.session_state.data_source or 'auto'}"
        )
    else:
        st.warning("No dataset loaded yet")
    st.markdown(
        """
        <div style="font-size:0.72rem; color:#A5D8D6; text-align:center; padding-top:0.8rem;">
            Turtle Insights • La Union, PH
        </div>
        """,
        unsafe_allow_html=True,
    )

df = st.session_state.turtle_df

if page_key == "overview":
    from views import overview
    overview.render(df)
elif page_key == "eggs":
    from views import eggs_forecast
    eggs_forecast.render(df)
elif page_key == "location":
    from views import location_forecast
    location_forecast.render(df)
elif page_key == "map":
    from views import nesting_map
    nesting_map.render(df)
elif page_key == "retrain":
    from views import model_mgmt
    model_mgmt.render(df)
