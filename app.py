# the python shit show continued is broght to you by app.py
from __future__ import annotations

# TODO
# fix the gap on the dashboard page
# remove big ugly bar introduced with streamlit pyhton libery. i tried st.set_page_config stuff, didnt work, look into this again when I lose the urge to k*ll myself (this is a joke)

# import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
import os
# from typing import Iterable, Sequence
import pandas as pd
import plotly.express as px
import streamlit as st
from assets.templates import (
    sidebar_brand,
    note_banner,
    home_about_card,
    home_usage_card,
    users_table_header,
)

APP_TITLE = "Giftyfy"
APP_SUBTITLE = "Gift choosing assistant"
DEFAULT_DB_PATH = Path(__file__).with_name("giftyfy.db")
NAV_PAGES = ("Home", "Dashboard", "Items", "Tables")
SCHEMA_DISPLAY_NAMES = {
    "users_login": "Users",
    "user_profiles": "Profiles",
    "items": "Items",
    "sales": "Sales",
}


def get_asset_path(filename: str) -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root / filename


def apply_global_style() -> None:
    try:
        css_path = get_asset_path("assets/style.css")
        css = css_path.read_text(encoding="utf-8")
    except Exception:
        css = ""
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def ensure_streamlit_dark_theme() -> None:
    return None


TABLE_NAMES = ("users_login", "user_profiles", "items", "sales")

# Item detail fields shown in the Items view.
SCORE_FIELDS = [
    "computing_devices_score",
    "peripherals_score",
    "displays_score",
    "storage_electronics_score",
    "audio_score",
    "video_score",
    "wearables_tech_score",
    "accessories_electronics_score",
    "power_charging_score",
    "furniture_score",
    "home_decor_score",
    "storage_home_score",
    "cleaning_score",
    "home_organization_score",
    "skincare_score",
    "personal_hygiene_score",
    "men_fashion_score",
    "women_fashion_score",
    "children_fashion_score",
    "fashion_general_score",
    "jewelry_score",
    "luxury_score",
    "toys_score",
    "educational_toys_score",
    "games_puzzles_score",
    "baby_gear_score",
    "pet_toys_score",
    "pet_health_score",
    "car_accessories_score",
    "car_vehicle_score",
    "power_tools_score",
    "hand_tools_score",
    "industrial_score",
    "safety_score",
    "gardening_supplies_score",
    "outdoor_score",
    "camping_score",
    "fitness_score",
    "books_score",
    "music_instruments_score",
    "movies_media_score",
]

GROUPED_SCORE_FIELDS = {
    "Electronics": (
        "computing_devices_score",
        "peripherals_score",
        "displays_score",
        "storage_electronics_score",
        "audio_score",
        "video_score",
        "wearables_tech_score",
        "accessories_electronics_score",
        "power_charging_score",
    ),
    "Home": (
        "furniture_score",
        "home_decor_score",
        "storage_home_score",
        "cleaning_score",
        "home_organization_score",
    ),
    "Personal care": ("skincare_score", "personal_hygiene_score"),
    "Fashion": (
        "men_fashion_score",
        "women_fashion_score",
        "children_fashion_score",
        "fashion_general_score",
    ),
    "Luxury": ("jewelry_score", "luxury_score"),
    "Children": (
        "toys_score",
        "educational_toys_score",
        "games_puzzles_score",
        "baby_gear_score",
    ),
    "Pets": ("pet_toys_score", "pet_health_score"),
    "Car": ("car_accessories_score", "car_vehicle_score"),
    "Outdoor": (
        "power_tools_score",
        "hand_tools_score",
        "industrial_score",
        "safety_score",
        "gardening_supplies_score",
        "outdoor_score",
        "camping_score",
        "fitness_score",
    ),
    "Creative": (
        "books_score",
        "music_instruments_score",
        "movies_media_score",
    ),
}
CATEGORY_COLORS = [
    "#ffd166",
    "#06d6a0",
    "#118ab2",
    "#f94144",
    "#9b5de5",
    "#f3722c",
    "#90be6d",
    "#4d7cf0",
    "#f9c74f",
    "#43aa8b",
]


def get_db_path() -> Path:
    custom_path = st.session_state.get("db_path")
    if custom_path:
        return Path(custom_path).expanduser()
    return DEFAULT_DB_PATH


def db_exists(db_path: Path) -> bool:
    return db_path.exists() and db_path.is_file()


def connect_db(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


@st.cache_data(show_spinner=False)
def fetch_dataframe(
    db_path_str: str, query: str, params: Sequence[object] | None = None
) -> pd.DataFrame:
    db_path = Path(db_path_str)
    with closing(connect_db(db_path)) as connection:
        return pd.read_sql_query(query, connection, params=params or ())


@st.cache_data(show_spinner=False)
def fetch_scalar(
    db_path_str: str,
    query: str,
    params: Sequence[object] | None = None,
    default: float = 0.0,
) -> float:
    db_path = Path(db_path_str)
    with closing(connect_db(db_path)) as connection:
        cursor = connection.execute(query, params or ())
        row = cursor.fetchone()
        if row is None:
            return default
        value = row[0]
        return float(value if value is not None else default)


@st.cache_data(show_spinner=False)
def table_row_count(db_path_str: str, table_name: str) -> int:
    return int(
        fetch_scalar(db_path_str, f"SELECT COUNT(*) FROM {table_name}", default=0)
    )


# return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0], tried doing table_row now table_row_count as inlne but it kept throwing an error, screw it and this sh***********


@st.cache_data(show_spinner=False)
def get_users_summary(db_path_str: str) -> pd.DataFrame:
    query = """
        SELECT
            u.user_id,
            u.username_,
            u.email_,
            u.is_admin,
            COUNT(p.profile_id) AS profile_count
        FROM users_login u
        LEFT JOIN user_profiles p ON p.user_id = u.user_id
        GROUP BY u.user_id, u.username_, u.email_, u.is_admin
        ORDER BY u.user_id
    """
    return fetch_dataframe(db_path_str, query)


@st.cache_data(show_spinner=False)
def get_profile_summary(db_path_str: str) -> pd.DataFrame:
    query = """
        SELECT
            p.profile_id,
            p.name_,
            p.user_id,
            u.username_,
            p.electronics_slider,
            p.home_slider,
            p.personal_care_slider,
            p.wearables_slider,
            p.luxury_slider,
            p.children_slider,
            p.pet_slider,
            p.car_slider,
            p.outdoor_slider,
            p.creative_slider
        FROM user_profiles p
        INNER JOIN users_login u ON u.user_id = p.user_id
        ORDER BY p.profile_id
    """
    return fetch_dataframe(db_path_str, query)


@st.cache_data(show_spinner=False)
def get_items_summary(
    db_path_str: str, item_id: int | None = None, item_name: str = ""
) -> pd.DataFrame:
    clauses: list[str] = []
    params: list[object] = []
    if item_id is not None:
        clauses.append("item_id = ?")
        params.append(item_id)
    if item_name.strip():
        clauses.append("LOWER(item_name) LIKE ?")
        params.append(f"%{item_name.strip().lower()}%")

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT
            item_id,
            item_name,
            retailer,
            associate_link,
            price,
            {", ".join(SCORE_FIELDS)}
        FROM items
        {where_sql}
        ORDER BY item_id
    """
    return fetch_dataframe(db_path_str, query, params)


@st.cache_data(show_spinner=False)
def get_sales_summary(db_path_str: str) -> pd.DataFrame:
    # yeah this is masically same as the last 2 iterations but i cant be asked to make generic, if you read this do it or you will regret it later
    query = """
        SELECT
            s.sale_id,
            s.user_id,
            u.username_ AS username,
            s.item_id,
            i.item_name,
            s.retailer_name,
            s.sale_price,
            s.commission_rate,
            s.profit,
            s.sold_at
        FROM sales s
        INNER JOIN users_login u ON u.user_id = s.user_id
        INNER JOIN items i ON i.item_id = s.item_id
        ORDER BY s.sale_id
    """
    return fetch_dataframe(db_path_str, query)


@st.cache_data(show_spinner=False)
def get_item_score_averages(
    db_path_str: str,
) -> pd.Series:  # no return type here, this i
    query = f"SELECT {', '.join(f'AVG({field}) AS {field}' for field in SCORE_FIELDS)} FROM items"
    frame = fetch_dataframe(db_path_str, query)
    return (
        frame.iloc[0]
        if not frame.empty
        else pd.Series({field: 0.0 for field in SCORE_FIELDS})
    )


@st.cache_data(show_spinner=False)
def get_sold_item_score_averages(db_path_str: str) -> pd.Series:
    query = f"""
        SELECT {", ".join(f"AVG(i.{field}) AS {field}" for field in SCORE_FIELDS)}
        FROM sales s
        INNER JOIN items i ON i.item_id = s.item_id
    """
    frame = fetch_dataframe(db_path_str, query)
    return (
        frame.iloc[0]
        if not frame.empty
        else pd.Series({field: 0.0 for field in SCORE_FIELDS})
    )


@st.cache_data(show_spinner=False)
def get_sales_by_retailer(db_path_str: str) -> pd.DataFrame:
    query = """
        SELECT retailer_name, COUNT(*) AS sale_count
        FROM sales
        GROUP BY retailer_name
        ORDER BY sale_count DESC, retailer_name ASC
        LIMIT 4
    """
    return fetch_dataframe(db_path_str, query)


@st.cache_data(show_spinner=False)
def get_sales_price_bands(db_path_str: str) -> pd.DataFrame:
    query = """
        WITH ranked AS (
            SELECT
                sale_price,
                NTILE(4) OVER (ORDER BY sale_price) AS price_band
            FROM sales
        )
        SELECT
            CASE price_band
                WHEN 1 THEN 'Budget'
                WHEN 2 THEN 'Standard'
                WHEN 3 THEN 'Premium'
                ELSE 'Elite'
            END AS band,
            COUNT(*) AS sale_count
        FROM ranked
        GROUP BY price_band
        ORDER BY price_band
    """
    # the sql stikes back with the fancy window function to create price bands; this is used for the sales price distribution chart
    return fetch_dataframe(db_path_str, query)


@st.cache_data(show_spinner=False)
def get_table_schema(db_path_str: str, table_name: str) -> pd.DataFrame:
    query = f"PRAGMA table_info({table_name})"
    return fetch_dataframe(db_path_str, query)


@st.cache_data(show_spinner=False)
def get_table_preview(
    db_path_str: str, table_name: str, limit: int = 25
) -> pd.DataFrame:
    query = f"SELECT * FROM {table_name} ORDER BY 1 LIMIT {int(limit)}"
    return fetch_dataframe(db_path_str, query)


@st.cache_data(show_spinner=False)
def get_metric_counts(db_path_str: str) -> dict[str, int]:
    return {table: table_row_count(db_path_str, table) for table in TABLE_NAMES}


@st.cache_data(show_spinner=False)
def get_profile_names(db_path_str: str) -> pd.DataFrame:
    query = "SELECT profile_id, name_, user_id FROM user_profiles ORDER BY profile_id"
    return fetch_dataframe(db_path_str, query)


@st.cache_data(show_spinner=False)
def get_user_lookup(db_path_str: str) -> pd.DataFrame:
    query = "SELECT user_id, username_ FROM users_login ORDER BY user_id"
    return fetch_dataframe(db_path_str, query)


@st.cache_data(show_spinner=False)
def get_item_names(db_path_str: str) -> pd.DataFrame:
    query = "SELECT item_id, item_name FROM items ORDER BY item_name"
    return fetch_dataframe(db_path_str, query)


def render_sidebar() -> str:
    st.sidebar.markdown(sidebar_brand(APP_TITLE), unsafe_allow_html=True)
    # Render navigation as large, styled buttons so they are clickable
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = NAV_PAGES[0]

    # Cceate a button for each page. Pressing a button updates session state.
    for p in NAV_PAGES:
        if st.sidebar.button(p, key=f"nav_{p}"):
            st.session_state["nav_page"] = p
    # remove the dotted list and keept a divider and gift box only
    # I had a great idea to also use javascript here, i pushed that idea so deep in my arse that i forgot about it, this is the best case senario for my mental health
    st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.sidebar.image(str(get_asset_path("assets/logo.png")), use_container_width=True)
    st.sidebar.markdown('<div style="height: 0.5rem"></div>', unsafe_allow_html=True)
    page = st.session_state.get("nav_page", NAV_PAGES[0])
    st.sidebar.markdown('<div style="height: 0.75rem"></div>', unsafe_allow_html=True)
    db_override = st.sidebar.text_input(
        "Database path",
        value=str(get_db_path()),
        help="Defaults to giftyfy.db beside app.py",
    )
    st.session_state["db_path"] = db_override
    return page


def render_small_metric(label: str, value: str, tone: str = "green") -> None:
    st.markdown(
        f"""
        <div class="metric-card {tone}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_page() -> None:
    st.markdown(f'<div class="hero-title">WELCOME</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ABOUT US</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="subtitle" style="text-align:center; max-width: 1100px; margin: 0 auto 1.4rem;">
            Giftyfy is a gift choosing assistant originally created as part of an enterprise computing assignment 3
            and built  to run locally with c++17, python, SQLite it suports many features such as allowing for many 
            users who posses profiles, item scoring and an algorith that matches profiles with items based on a quiz 
            which features questions and interactive sliders, and sales reporting and a dashboard to analyse user 
            data sales.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        note_banner(),
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.15, 1.0], gap="large")
    with left:
        st.markdown(home_about_card(), unsafe_allow_html=True)
    with right:
        st.markdown(home_usage_card(), unsafe_allow_html=True)


def render_dashboard_page(db_path: Path) -> None:
    counts = get_metric_counts(str(db_path))
    users_df = get_users_summary(str(db_path))
    sales_df = get_sales_summary(str(db_path))

    total_users = counts["users_login"]
    total_profiles = counts["user_profiles"]
    total_sales = counts["sales"]
    total_items = counts["items"]

    avg_sale_price = float(sales_df["sale_price"].mean()) if not sales_df.empty else 0.0
    avg_commission = (
        float(sales_df["commission_rate"].mean()) if not sales_df.empty else 0.0
    )
    avg_commission_amount = (
        float((sales_df["sale_price"] * sales_df["commission_rate"]).mean())
        if not sales_df.empty
        else 0.0
    )
    total_profit = float(sales_df["profit"].sum()) if not sales_df.empty else 0.0

    st.markdown(
        '<div class="section-title" style="text-align:center; margin-bottom: 1rem;">DASHBOARD</div>',
        unsafe_allow_html=True,
    )

    # Single row: left metrics | middle metrics | charts (all start at the same top)
    left_col, middle_col, chart_col = st.columns([1.1, 1.55, 1.08], gap="large")

    with left_col:
        render_small_metric("number of users", f"{total_users} users")
        st.markdown('<div style="height: 0.8rem"></div>', unsafe_allow_html=True)
        render_small_metric("number of profiles", f"{total_profiles}")
        st.markdown('<div style="height: 0.8rem"></div>', unsafe_allow_html=True)
        render_small_metric("profit", f"${total_profit:,.0f}")

    with middle_col:
        render_small_metric("avrg sale price", f"${avg_sale_price:,.0f}", tone="teal")
        st.markdown('<div style="height: 0.8rem"></div>', unsafe_allow_html=True)
        render_small_metric(
            "average comision rate", f"{avg_commission:.0%}", tone="teal"
        )
        st.markdown('<div style="height: 0.8rem"></div>', unsafe_allow_html=True)
        render_small_metric(
            "average comision", f"${avg_commission_amount:,.1f}", tone="teal"
        )
        st.markdown('<div style="height: 0.4rem"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height: 0.25rem"></div>', unsafe_allow_html=True)
    wide_col, _ = st.columns([1.1 + 1.55, 1.08], gap="large")

    with wide_col:
        st.markdown('<div style="height: 0.4rem"></div>', unsafe_allow_html=True)
        # placed here so the KPI spans the same width as the users table below
        # (moved from the top-row to avoid a large vertical gap)
        render_small_metric("number of sales", f"{total_sales}", tone="teal")
        st.markdown('<div style="height: 0.35rem"></div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                '<span class="card-marker table-card-marker"></span>',
                unsafe_allow_html=True,
            )
            st.markdown(users_table_header(), unsafe_allow_html=True)
            st.dataframe(
                users_df, use_container_width=True, height=180, hide_index=True
            )

    with chart_col:
        item_avg_scores = get_item_score_averages(str(db_path))
        sold_avg_scores = get_sold_item_score_averages(str(db_path))

        item_pie_df = pd.DataFrame(
            {
                "category": list(GROUPED_SCORE_FIELDS.keys()),
                "score": [
                    float(item_avg_scores[list(fields)].mean()) if fields else 0.0
                    for fields in GROUPED_SCORE_FIELDS.values()
                ],
            }
        )
        item_pie_df["score"] = item_pie_df["score"].fillna(0.0)

        sold_pie_df = pd.DataFrame(
            {
                "category": list(GROUPED_SCORE_FIELDS.keys()),
                "score": [
                    float(sold_avg_scores[list(fields)].mean()) if fields else 0.0
                    for fields in GROUPED_SCORE_FIELDS.values()
                ],
            }
        )
        sold_pie_df["score"] = sold_pie_df["score"].fillna(0.0)

        if item_pie_df["score"].sum() <= 0:
            item_pie_df = pd.DataFrame({"category": ["No data"], "score": [1.0]})
        if sold_pie_df["score"].sum() <= 0:
            sold_pie_df = pd.DataFrame({"category": ["No sales yet"], "score": [1.0]})

        chart1 = px.pie(
            item_pie_df,
            values="score",
            names="category",
            hole=0.0,
            color_discrete_sequence=CATEGORY_COLORS,
        )
        _legend_cfg = dict(
            font=dict(size=10),
            orientation="v",
            x=1.01,
            y=0.5,
            xanchor="left",
            yanchor="middle",
        )
        chart1.update_layout(
            title="items score distribution",
            paper_bgcolor="#b5628e",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f7e8c2", size=12),
            margin=dict(l=0, r=0, t=40, b=0),
            height=240,
            showlegend=True,
            legend=_legend_cfg,
            title_x=0.04,
        )
        chart1.update_traces(
            textposition="inside",
            textinfo="percent",
            marker=dict(line=dict(color="#3b3634", width=1)),
        )

        chart2 = px.pie(
            sold_pie_df,
            values="score",
            names="category",
            hole=0.0,
            color_discrete_sequence=CATEGORY_COLORS,
        )
        chart2.update_layout(
            title="sold items score distribution",
            paper_bgcolor="#b5628e",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f7e8c2", size=12),
            margin=dict(l=0, r=0, t=40, b=0),
            height=240,
            showlegend=True,
            legend=_legend_cfg,
            title_x=0.04,
        )
        chart2.update_traces(
            textposition="inside",
            textinfo="percent",
            marker=dict(line=dict(color="#3b3634", width=1)),
        )

        st.plotly_chart(
            chart1, use_container_width=True, config={"displayModeBar": False}
        )
        st.markdown('<div style="height: 0.5rem"></div>', unsafe_allow_html=True)
        st.plotly_chart(
            chart2, use_container_width=True, config={"displayModeBar": False}
        )


def render_items_page(db_path: Path) -> None:
    st.markdown(
        '<div class="section-title" style="text-align:center; margin-bottom: 1rem;">ITEMS</div>',
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.28, 1.0], gap="large")  # majic number for fun

    with left_col:
        # Big header card containing the ID input
        with st.container(border=True):
            st.markdown(
                '<span class="card-marker search-card-marker"></span>',
                unsafe_allow_html=True,
            )
            # st.markdown(
            #    '<div style="font-size:2rem; font-weight:800; text-align:center; padding:0.6rem 0;">user input</div>',
            #    unsafe_allow_html=True,
            # )
            item_id = st.number_input(
                "query by ID",
                min_value=0,
                step=1,
                value=0,
                help="Enter an item_id to narrow the item search",
            )
        st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(
                '<span class="card-marker search-card-compact-marker"></span>',
                unsafe_allow_html=True,
            )
            # the reason i use a separate backing key so chip buttons can write to it
            # without conflicting with the widget that owns "item_name_query".
            if "_item_name_backing" not in st.session_state:
                st.session_state["_item_name_backing"] = ""

            def _sync_from_widget() -> None:
                st.session_state["_item_name_backing"] = st.session_state[
                    "item_name_query"
                ]

            item_name_query = st.text_input(
                "query by name",
                value=st.session_state["_item_name_backing"],
                key="item_name_query",
                placeholder="Type to filter suggestions (autocomplete)",
                on_change=_sync_from_widget,
            )

            try:
                names_df = get_item_names(str(db_path))
            except Exception:
                names_df = pd.DataFrame(columns=["item_id", "item_name"])

            suggestions: list[str] = []
            if item_name_query and not names_df.empty:
                lower = item_name_query.strip().lower()
                mask = names_df["item_name"].str.lower().str.contains(lower, na=False)
                suggestions = names_df.loc[mask, "item_name"].head(15).tolist()
            elif not names_df.empty:
                suggestions = names_df["item_name"].head(15).tolist()

            # render suggestion buttons in rows of 3; clicking a chip fills the text input.
            if suggestions:
                chips_per_row = 3
                cols = [
                    st.columns(chips_per_row)
                    for _ in range(
                        (len(suggestions) + chips_per_row - 1) // chips_per_row
                    )
                ]
                for idx, s in enumerate(suggestions):
                    row = cols[idx // chips_per_row]
                    col = row[idx % chips_per_row]
                    if col.button(s, key=f"suggest_{idx}"):
                        # only write to the backing key only and never the fkn never the widget key
                        st.session_state["_item_name_backing"] = s
                        st.rerun()

        # use the backing key so chip selections are picked up immediately as per previous instructions
        # yes i take my own advice whenever i want to (should be more often).
        item_name = st.session_state.get("_item_name_backing", "")

        search_id = int(item_id) if item_id > 0 else None
        results = get_items_summary(
            str(db_path), item_id=search_id, item_name=item_name
        )
        if results.empty:
            st.markdown(
                """
                <div class="item-detail-card">
                    <div style="text-align:center; font-size: 1.6rem; font-weight: 800;">No matching items</div>
                    <div style="text-align:center; margin-top: 0.6rem;">Try a different id or part of an item name.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            selected = results.iloc[0]
            associate_link = str(selected["associate_link"] or "")
            link_html = (
                f"<a href='{associate_link}' target='_blank'>{associate_link}</a>"
                if associate_link
                else "<span>None</span>"
            )
            price_value = (
                f"${float(selected['price']):,.2f}"
                if pd.notna(selected["price"])
                else ""
            )
            st.markdown(
                f"""
                <div class="item-detail-card">
                    <div class="item-detail-row"><span>item ID</span><span>{int(selected["item_id"])}</span></div>
                    <div class="item-detail-row"><span>Item name</span><span>{selected["item_name"]}</span></div>
                    <div class="item-detail-row"><span>retailer</span><span>{selected["retailer"] or ""}</span></div>
                    <div class="item-detail-row"><span>associate link</span><span class="item-link">{link_html}</span></div>
                    <div class="item-detail-row"><span>price</span><span>{price_value}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    # I will not k*** myself, I will not k*** myslef, it is only a small amout of python, 1000 lines in and i will not k*** myself.
    with right_col:
        if results.empty:
            st.markdown(
                """
                <div class="scroll-card">
                    <div style="font-size: 1.4rem; font-weight: 800; margin-bottom: 0.6rem;">score metrics</div>
                    <div class="small-note">No item selected.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            row = results.iloc[0]
            score_rows = "".join(
                f'<div class="score-item"><span>• {field.replace("_score", "").replace("_", " ").title()}</span>'
                f"<span>{int(row[field]) if pd.notna(row[field]) else 0}</span></div>"
                for field in SCORE_FIELDS
            )
            st.markdown(
                f"""
                <div class="scroll-card">
                    <div style="font-size: 1.4rem; font-weight: 800; margin-bottom: 0.6rem;">score metrics</div>
                    {score_rows}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_tables_page(db_path: Path) -> None:
    st.markdown(
        '<div class="section-title" style="text-align:center; margin-bottom: 1rem;">DATABASE TABLES</div>',
        unsafe_allow_html=True,
    )

    counts = get_metric_counts(str(db_path))
    kpi_cols = st.columns(4, gap="small")
    metric_specs = [
        ("Users", counts["users_login"], "green"),
        ("Profiles", counts["user_profiles"], "green"),
        ("Items", counts["items"], "teal"),
        ("Sales", counts["sales"], "teal"),
    ]
    for column, (label, value, tone) in zip(kpi_cols, metric_specs, strict=False):
        with column:
            render_small_metric(label, str(value), tone=tone)

    st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)
    # Let the user choose which table to inspect
    display_names = [SCHEMA_DISPLAY_NAMES[name] for name in TABLE_NAMES]
    display_to_table = {SCHEMA_DISPLAY_NAMES[name]: name for name in TABLE_NAMES}
    selected_display = st.selectbox("Choose table to view", display_names, index=0)
    table_name = display_to_table[selected_display]

    schema = get_table_schema(str(db_path), table_name)
    preview = get_table_preview(str(db_path), table_name, limit=50)
    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown(
                '<span class="card-marker table-card-marker"></span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="font-size:1.25rem; font-weight:800; margin-bottom:0.5rem;">{SCHEMA_DISPLAY_NAMES[table_name]} schema</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(schema, use_container_width=True, hide_index=True, height=300)
    with right:
        with st.container(border=True):
            st.markdown(
                '<span class="card-marker table-card-marker"></span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="font-size:1.25rem; font-weight:800; margin-bottom:0.5rem;">{SCHEMA_DISPLAY_NAMES[table_name]} preview</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(preview, use_container_width=True, hide_index=True, height=300)


def render_not_found_state(db_path: Path) -> None:
    st.markdown('<div class="hero-title">WELCOME</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="home-card" style="background: rgba(255,255,255,0.03); border-radius: 1.8rem; padding: 1.4rem 1.5rem;">
            <div style="font-size: 1.8rem; font-weight: 800; color: var(--accent); margin-bottom: 0.6rem;">Database not found</div>
            <div style="font-size: 1.15rem; line-height: 1.6;">
                I looked for <b>{db_path}</b> but could not open it.<br>
                Create the SQLite file with the provided schema or change the database path in the sidebar.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    ensure_streamlit_dark_theme()
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🎁",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_global_style()
    page = render_sidebar()
    db_path = get_db_path()

    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom: 0.4rem; color: var(--accent); font-size: 1.1rem; font-weight: 700;">
            {APP_SUBTITLE}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not db_exists(db_path):
        render_not_found_state(db_path)
        return

    try:
        if page == "Home":
            render_home_page()
        elif page == "Dashboard":
            render_dashboard_page(db_path)
        elif page == "Items":
            render_items_page(db_path)
        elif page == "Tables":
            render_tables_page(db_path)
        else:
            st.info("Choose a page from the sidebar.")
    except sqlite3.Error as exc:
        st.error(f"SQLite error while loading {page.lower()} view: {exc}")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Unexpected error while rendering {page.lower()} view: {exc}")


# now you can take your keyboard out you ass, the pyhton shitshow is over

if __name__ == "__main__":
    main()
