"""
Interactive Nesting Map – Folium
"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.theme import COLORS
from utils.data_loader import BARANGAY_COORDS, BARANGAY_MAPPING, SHORT_NAMES, apply_filters, get_filter_options

try:
    import folium
    from streamlit_folium import st_folium
    from folium.plugins import MarkerCluster, HeatMap
    FOLIUM_OK = True
except ImportError:
    FOLIUM_OK = False


def render(df: pd.DataFrame):
    st.markdown(
        """
        <div class="main-header">
            <h1>🗺️ Nesting Map</h1>
            <p>Geographic view of nesting activity across Bacnotan & San Juan, La Union</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not FOLIUM_OK:
        st.error("folium / streamlit-folium not installed. Run: pip install folium streamlit-folium")
        return

    if df is None or df.empty:
        st.markdown(
            '<div class="info-box"><strong>No dataset loaded.</strong> Upload the Excel file to see nest counts on the map.</div>',
            unsafe_allow_html=True,
        )
        # Still show base map of the 12 barangays
        _render_base_map()
        return

    # Filters
    opts = get_filter_options(df)
    f1, f2, f3 = st.columns(3)
    with f1:
        years = opts.get("years", [])
        sel_years = st.multiselect("Year", years, default=years, key="map_years")
    with f2:
        months = opts.get("months", list(range(1, 13)))
        month_labels = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
        sel_months = st.multiselect(
            "Month", months,
            format_func=lambda m: month_labels.get(m, str(m)),
            default=months, key="map_months",
        )
    with f3:
        map_style = st.selectbox("Map style", ["Markers + Circles", "Heatmap", "Both"], key="map_style")

    filtered = apply_filters(df, years=sel_years or None, months=sel_months or None)

    # Aggregate by location
    if "L_TAGNUM" not in filtered.columns:
        st.warning("L_TAGNUM column missing.")
        _render_base_map()
        return

    agg = (
        filtered.groupby("L_TAGNUM")
        .agg(
            nests=("DATE LAID", "count"),
            eggs=("NO. OF EGGS LAID", "sum") if "NO. OF EGGS LAID" in filtered.columns else ("DATE LAID", "count"),
            avg_eggs=("NO. OF EGGS LAID", "mean") if "NO. OF EGGS LAID" in filtered.columns else ("DATE LAID", "count"),
        )
        .reset_index()
    )
    agg["barangay"] = agg["L_TAGNUM"].map(BARANGAY_MAPPING)
    agg["short"] = agg["L_TAGNUM"].map(SHORT_NAMES)
    agg["lat"] = agg["L_TAGNUM"].map(lambda x: BARANGAY_COORDS.get(x, (16.72, 120.35))[0])
    agg["lon"] = agg["L_TAGNUM"].map(lambda x: BARANGAY_COORDS.get(x, (16.72, 120.35))[1])

    # KPI strip — all four cards share the same kpi-card height/style
    top3 = agg.sort_values("nests", ascending=False).head(3)
    locs_n = len(agg[agg["nests"] > 0])
    nests_n = int(agg["nests"].sum())
    eggs_n = int(agg["eggs"].sum()) if "eggs" in agg.columns else 0
    medals = ["🥇", "🥈", "🥉"]
    if len(top3):
        top_lines = []
        for i, (_, r) in enumerate(top3.iterrows()):
            name = r.get("short") or SHORT_NAMES.get(int(r["L_TAGNUM"]), str(r["L_TAGNUM"]))
            top_lines.append(f"{medals[i]} {name} ({int(r['nests'])})")
        top_body = "<br>".join(top_lines)
    else:
        top_body = "—"

    def _card(label, value_html):
        return (
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value' style='font-size:1.55rem;'>{value_html}</div>"
            f"</div>"
        )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(_card("Locations with nests", f"{locs_n}"), unsafe_allow_html=True)
    with k2:
        st.markdown(_card("Total nests (filtered)", f"{nests_n:,}"), unsafe_allow_html=True)
    with k3:
        st.markdown(_card("Total eggs (filtered)", f"{eggs_n:,}"), unsafe_allow_html=True)
    with k4:
        st.markdown(
            "<div class='kpi-card'>"
            "<div class='kpi-label'>Top 3 nesting barangays</div>"
            f"<div class='kpi-value' style='font-size:0.92rem;line-height:1.35;font-weight:600;'>{top_body}</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    # Build map
    center_lat = 16.71
    center_lon = 120.345

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="CartoDB positron",
        control_scale=True,
    )

    # Alternative tiles
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite",
        overlay=False,
    ).add_to(m)

    max_nests = agg["nests"].max() if len(agg) else 1
    max_nests = max(max_nests, 1)

    if map_style in ["Markers + Circles", "Both"]:
        for _, row in agg.iterrows():
            if pd.isna(row["lat"]) or pd.isna(row["lon"]):
                continue
            radius = 8 + 25 * (row["nests"] / max_nests)
            color = COLORS["sea_teal"] if row["nests"] > 0 else "#94A3B8"
            popup_html = f"""
            <div style="font-family:Segoe UI,sans-serif; min-width:180px;">
                <b style="color:#0A2647; font-size:1.05rem;">{row['short']}</b><br>
                <span style="color:#64748B; font-size:0.85rem;">{row['barangay']}</span><br>
                <hr style="margin:6px 0; border:none; border-top:1px solid #E2E8F0;">
                <b>Nests:</b> {int(row['nests'])}<br>
                <b>Total Eggs:</b> {int(row.get('eggs', 0))}<br>
                <b>Avg Eggs:</b> {row.get('avg_eggs', 0):.1f}
            </div>
            """
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=radius,
                color=COLORS["deep_ocean"],
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.75,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"{row['short']}: {int(row['nests'])} nests",
            ).add_to(m)

            # Small label
            folium.Marker(
                location=[row["lat"], row["lon"]],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="font-size:10px; font-weight:600; color:#0A2647;
                                text-shadow:0 0 3px white, 0 0 3px white; white-space:nowrap;">
                        {row['short']}
                    </div>
                    """,
                    icon_size=(80, 20),
                    icon_anchor=(40, -5),
                ),
            ).add_to(m)

    if map_style in ["Heatmap", "Both"] and len(agg) > 0:
        heat_data = [
            [row["lat"], row["lon"], row["nests"]]
            for _, row in agg.iterrows()
            if row["nests"] > 0 and not pd.isna(row["lat"])
        ]
        if heat_data:
            HeatMap(
                heat_data,
                radius=28,
                blur=22,
                min_opacity=0.35,
                gradient={0.2: "#E8F6F3", 0.5: "#14919B", 0.8: "#0D7377", 1.0: "#0A2647"},
            ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed; bottom:40px; left:40px; z-index:1000;
                background:white; padding:10px 14px; border-radius:10px;
                box-shadow:0 2px 10px rgba(0,0,0,0.15); font-size:12px;
                font-family:Segoe UI,sans-serif; border-left:4px solid #0D7377;">
        <b style="color:#0A2647;">Nest density</b><br>
        Circle size ∝ number of nests<br>
        <span style="color:#0D7377;">●</span> Active site &nbsp;
        <span style="color:#94A3B8;">●</span> No nests in filter
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl().add_to(m)

    st_folium(m, width=None, height=520, returned_objects=[])

    # Side table
    st.markdown('<div class="section-card"><div class="section-title">Nest Counts by Barangay</div>', unsafe_allow_html=True)
    table = agg[["L_TAGNUM", "short", "barangay", "nests", "eggs", "avg_eggs"]].copy()
    table.columns = ["Code", "Short Name", "Full Barangay", "Nests", "Total Eggs", "Avg Eggs/Nest"]
    table = table.sort_values("Nests", ascending=False)
    table["Avg Eggs/Nest"] = table["Avg Eggs/Nest"].round(1)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        "Coordinates are approximate coastal positions for visualization. "
        "Actual nest GPS points (if available) can replace these in a future version."
    )


def _render_base_map():
    """Show the 12 barangays even without data."""
    m = folium.Map(location=[16.71, 120.345], zoom_start=12, tiles="CartoDB positron")
    for code, (lat, lon) in BARANGAY_COORDS.items():
        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            color=COLORS["deep_ocean"],
            fill=True,
            fill_color=COLORS["sea_teal"],
            fill_opacity=0.7,
            popup=BARANGAY_MAPPING.get(code, str(code)),
            tooltip=SHORT_NAMES.get(code, str(code)),
        ).add_to(m)
    st_folium(m, width=None, height=480, returned_objects=[])
    st.info("Upload dataset to see nest counts and heatmap.")
