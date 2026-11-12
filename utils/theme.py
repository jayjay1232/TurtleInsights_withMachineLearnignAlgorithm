"""
Sea-themed color palette and CSS for Turtle Analytical Insights
"""

COLORS = {
    "deep_ocean": "#0A2647",
    "sea_teal": "#0D7377",
    "bright_sea": "#14919B",
    "seafoam": "#E8F6F3",
    "light_bg": "#F0F9F8",
    "sand": "#F4A261",
    "coral": "#E76F51",
    "text": "#0F172A",
    "white": "#FFFFFF",
    "soft_teal": "#2A9D8F",
    "muted": "#64748B",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
}

PLOTLY_SEQ = ["#0A2647", "#0D7377", "#14919B", "#2A9D8F", "#E8F6F3"]
PLOTLY_CAT = ["#0D7377", "#14919B", "#F4A261", "#E76F51", "#2A9D8F", "#0A2647"]

CUSTOM_CSS = f"""
<style>
    .stApp {{
        background: linear-gradient(180deg, {COLORS['light_bg']} 0%, {COLORS['seafoam']} 100%);
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"],
    div[data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLORS['deep_ocean']} 0%, {COLORS['sea_teal']} 100%);
        border-right: 3px solid {COLORS['bright_sea']};
    }}
    [data-testid="stSidebar"] * {{
        color: {COLORS['seafoam']} !important;
    }}
    [data-testid="stSidebar"] .stRadio label {{
        color: {COLORS['seafoam']} !important;
        font-weight: 500;
        padding: 0.35rem 0.5rem;
        border-radius: 8px;
    }}
    [data-testid="stSidebar"] .stRadio label:hover {{
        background: rgba(255,255,255,0.08);
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {{
        background: rgba(255,255,255,0.10) !important;
        border: 1px solid rgba(232,246,243,0.35) !important;
        border-radius: 12px !important;
        padding: 0.6rem !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section {{
        background: transparent !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploader"] label,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] small,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] span,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] p {{
        color: {COLORS['seafoam']} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
        background: rgba(10, 38, 71, 0.35) !important;
        border: 1px dashed rgba(232,246,243,0.45) !important;
        color: {COLORS['seafoam']} !important;
    }}
    [data-testid="stSidebar"] .stAlert {{
        background: rgba(10, 38, 71, 0.55) !important;
        color: {COLORS['seafoam']} !important;
    }}
    [data-testid="stSidebar"] .stAlert * {{
        color: {COLORS['seafoam']} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stCaption"] {{
        color: {COLORS['seafoam']} !important;
        opacity: 0.95;
    }}

    
    [data-baseweb="tag"],
    span[data-baseweb="tag"],
    div[data-baseweb="tag"],
    [data-baseweb="select"] [data-baseweb="tag"],
    .stMultiSelect [data-baseweb="tag"],
    div[data-testid="stMultiSelect"] [data-baseweb="tag"],
    div[data-testid="stSidebar"] [data-baseweb="tag"] {{
        background-color: #0D7377 !important;
        background-image: none !important;
        color: #FFFFFF !important;
        border: 0 !important;
        border-radius: 8px !important;
    }}
    [data-baseweb="tag"] span,
    [data-baseweb="tag"] div,
    [data-baseweb="tag"] p {{
        color: #FFFFFF !important;
    }}
    [data-baseweb="tag"] svg,
    [data-baseweb="tag"] path {{
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }}
    [data-baseweb="menu"] li[aria-selected="true"] {{
        background-color: #14919B !important;
        color: #FFFFFF !important;
    }}

    .main-header {{
        background: linear-gradient(135deg, {COLORS['deep_ocean']} 0%, {COLORS['sea_teal']} 50%, {COLORS['bright_sea']} 100%);
        padding: 1.6rem 1.8rem;
        border-radius: 16px;
        margin-bottom: 1.25rem;
        box-shadow: 0 8px 24px rgba(10, 38, 71, 0.25);
        color: white;
    }}
    .main-header h1 {{
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
        color: white !important;
    }}
    .main-header p {{
        margin: 0.35rem 0 0 0;
        opacity: 0.92;
        font-size: 1rem;
        color: {COLORS['seafoam']} !important;
    }}
    .insight-box {{
        background: linear-gradient(135deg, #FFFFFF 0%, {COLORS['seafoam']} 100%);
        border: 1px solid rgba(20, 145, 155, 0.25);
        border-left: 5px solid {COLORS['bright_sea']};
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0 1.25rem 0;
        color: {COLORS['text']};
        font-size: 0.98rem;
        line-height: 1.45;
    }}
    .insight-box strong {{ color: {COLORS['deep_ocean']}; }}
    .kpi-card {{
        background: white;
        border-radius: 14px;
        padding: 1.0rem 1.15rem;
        box-shadow: 0 4px 14px rgba(13, 115, 119, 0.12);
        border-left: 5px solid {COLORS['sea_teal']};
        height: 118px;
        min-height: 118px;
        max-height: 118px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-sizing: border-box;
        overflow: hidden;
    }}
    .kpi-card .kpi-label {{
        font-size: 0.78rem;
        color: {COLORS['muted']};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 0.3rem;
    }}
    .kpi-card .kpi-value {{
        font-size: 1.55rem;
        font-weight: 700;
        color: {COLORS['deep_ocean']};
        line-height: 1.15;
    }}
    .section-card {{
        background: white;
        border-radius: 14px;
        padding: 1.35rem;
        box-shadow: 0 4px 14px rgba(13, 115, 119, 0.10);
        margin-bottom: 1.15rem;
        border: 1px solid rgba(20, 145, 155, 0.15);
    }}
    .section-title {{
        font-size: 1.15rem;
        font-weight: 650;
        color: {COLORS['deep_ocean']};
        margin-bottom: 0.85rem;
    }}
    .filter-panel {{
        background: white;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 1.15rem;
        box-shadow: 0 2px 10px rgba(13, 115, 119, 0.08);
        border: 1px solid rgba(20, 145, 155, 0.14);
    }}
    .stMultiSelect [data-baseweb="select"] > div {{
        border-color: rgba(20, 145, 155, 0.35) !important;
        background: {COLORS['seafoam']} !important;
    }}
    .stSelectbox [data-baseweb="select"] > div {{
        border-color: rgba(20, 145, 155, 0.35) !important;
    }}
    .stMultiSelect label, .stSelectbox label, .stSlider label {{
        color: {COLORS['deep_ocean']} !important;
        font-weight: 600 !important;
    }}
    .stButton > button {{
        background: linear-gradient(135deg, {COLORS['sea_teal']} 0%, {COLORS['bright_sea']} 100%);
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 0.55rem 1.35rem;
        font-weight: 600;
        box-shadow: 0 3px 10px rgba(13, 115, 119, 0.25);
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, {COLORS['deep_ocean']} 0%, {COLORS['sea_teal']} 100%);
        color: white !important;
    }}
    [data-testid="stMetric"] {{
        background: white;
        padding: 0.85rem 1.05rem;
        border-radius: 14px;
        box-shadow: 0 3px 10px rgba(13, 115, 119, 0.1);
        border-left: 5px solid {COLORS['sea_teal']};
        height: 118px;
        min-height: 118px;
        max-height: 118px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-sizing: border-box;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {COLORS['sea_teal']}, {COLORS['bright_sea']});
        color: white !important;
    }}
    .info-box {{
        background: linear-gradient(135deg, {COLORS['seafoam']} 0%, white 100%);
        border-left: 4px solid {COLORS['bright_sea']};
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin: 0.85rem 0;
        color: {COLORS['text']};
    }}
    .success-box {{
        background: linear-gradient(135deg, #ECFDF5 0%, white 100%);
        border-left: 4px solid {COLORS['success']};
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin: 0.85rem 0;
    }}
    .app-footer {{
        text-align: center;
        padding: 1.25rem;
        color: {COLORS['muted']};
        font-size: 0.85rem;
        margin-top: 1.5rem;
        border-top: 1px solid rgba(20, 145, 155, 0.15);
    }}
</style>
"""


def chart_layout(**kwargs):
    """Dark readable axis/legend text on white plot backgrounds."""
    base = dict(
        font=dict(color="#0A2647", size=13),
        plot_bgcolor="rgba(255,255,255,1)",
        paper_bgcolor="rgba(255,255,255,0)",
        xaxis=dict(
            title_font=dict(color="#0A2647", size=13),
            tickfont=dict(color="#0A2647", size=12),
            gridcolor="rgba(10,38,71,0.12)",
            linecolor="rgba(10,38,71,0.35)",
            zerolinecolor="rgba(10,38,71,0.25)",
        ),
        yaxis=dict(
            title_font=dict(color="#0A2647", size=13),
            tickfont=dict(color="#0A2647", size=12),
            gridcolor="rgba(10,38,71,0.12)",
            linecolor="rgba(10,38,71,0.35)",
            zerolinecolor="rgba(10,38,71,0.25)",
        ),
        legend=dict(font=dict(color="#0A2647", size=12)),
        title_font=dict(color="#0A2647", size=15),
        coloraxis_colorbar=dict(
            tickfont=dict(color="#0A2647"),
            title_font=dict(color="#0A2647"),
        ),
    )
    for k, v in kwargs.items():
        if k in ("xaxis", "yaxis", "yaxis2", "legend") and isinstance(v, dict) and isinstance(base.get(k), dict):
            merged = dict(base[k])
            merged.update(v)
            base[k] = merged
        else:
            base[k] = v
    return base


def inject_theme():
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
