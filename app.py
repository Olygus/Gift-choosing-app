# the python shit show continued is broght to you by app.py
from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd
import plotly.express as px
import streamlit as st

APP_TITLE = "Giftyfy"
APP_SUBTITLE = "Gift choosing assistant"
DEFAULT_DB_PATH = Path(__file__).with_name("giftyfy.db")

TABLE_NAMES = ("users_login", "user_profiles", "items", "sales")

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
    "Tech": [
        "computing_devices_score",
        "peripherals_score",
        "displays_score",
        "storage_electronics_score",
        "audio_score",
        "video_score",
        "wearables_tech_score",
        "accessories_electronics_score",
        "power_charging_score",
    ],
    "Home": [
        "furniture_score",
        "home_decor_score",
        "storage_home_score",
        "cleaning_score",
        "home_organization_score",
    ],
    "Lifestyle": [
        "skincare_score",
        "personal_hygiene_score",
        "men_fashion_score",
        "women_fashion_score",
        "children_fashion_score",
        "fashion_general_score",
        "jewelry_score",
        "luxury_score",
        "books_score",
        "music_instruments_score",
        "movies_media_score",
    ],
    "Practical": [
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
    ],
}

CATEGORY_GROUPS = [
    (
        "Electronics",
        [
            "computing_devices_score",
            "peripherals_score",
            "displays_score",
            "storage_electronics_score",
            "audio_score",
            "video_score",
            "wearables_tech_score",
            "accessories_electronics_score",
            "power_charging_score",
        ],
    ),
    (
        "Home",
        [
            "furniture_score",
            "home_decor_score",
            "storage_home_score",
            "cleaning_score",
            "home_organization_score",
        ],
    ),
    (
        "Care",
        [
            "skincare_score",
            "personal_hygiene_score",
            "men_fashion_score",
            "women_fashion_score",
            "children_fashion_score",
            "fashion_general_score",
        ],
    ),
    (
        "Family",
        [
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
        ],
    ),
]

SCHEMA_DISPLAY_NAMES = {
    "users_login": "Users",
    "user_profiles": "Profiles",
    "items": "Items",
    "sales": "Sales",
}

NAV_PAGES = ("Home", "Dashboard", "Items", "Tables")


# when you think the css nighmare is over but this shit needs to be done, honestly iy is better that what i was cooking in c++
def apply_global_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #3b3634;
            --bg-elevated: #4a4340;
            --sidebar: #d16413;
            --card-green: #4a7a64;
            --card-teal: #4d8d97;
            --card-orange: #f2bc67;
            --card-pink: #b5628e;
            --panel: #f4bf68;
            --text: #f7e8c2;
            --muted: #e6d2a7;
            --accent: #ffb561;
            --grid: #ff9ea4;
        }

        html, body, [class*="css"]  {
            font-family: "Trebuchet MS", "Segoe UI", sans-serif;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        section[data-testid="stSidebar"] {
            background: var(--sidebar);
        }

        section[data-testid="stSidebar"] > div {
            background: var(--sidebar);
        }

        footer {
            display: none;
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1.2rem;
        }

        .page-shell {
            background: var(--bg);
            color: var(--text);
        }

        .hero-title {
            text-align: center;
            color: var(--accent);
            font-size: clamp(2.8rem, 5vw, 4.6rem);
            font-weight: 800;
            letter-spacing: 0.03em;
            margin: 0.25rem 0 0.4rem;
        }

        .section-title {
            color: var(--accent);
            font-size: clamp(2rem, 4vw, 3.4rem);
            font-weight: 800;
            margin: 0.15rem 0 0.4rem;
            letter-spacing: 0.02em;
        }

        .subtitle {
            color: var(--text);
            font-size: 1.1rem;
            line-height: 1.5;
        }

        .note-banner {
            display: inline-block;
            background: #f0281e;
            color: #fff4d7;
            padding: 0.35rem 1rem;
            border-radius: 0.3rem;
            font-size: 2rem;
            font-weight: 900;
            letter-spacing: 0.02em;
            margin-right: 0.65rem;
        }

        .note-line {
            color: var(--accent);
            font-size: 2rem;
            font-weight: 800;
        }

        .metric-card,
        .chart-card,
        .table-card,
        .search-card,
        .item-detail-card,
        .scroll-card,
        .home-card {
            border-radius: 1.6rem;
            padding: 1rem 1.1rem;
            box-shadow: 0 0 0 1px rgba(255,255,255,0.03) inset;
        }

        .metric-card {
            background: var(--card-green);
            color: var(--text);
            text-align: center;
            min-height: 7.1rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 0.2rem;
        }

        .metric-card.teal {
            background: var(--card-teal);
        }

        .metric-card.orange {
            background: var(--card-orange);
            color: #fff6d7;
        }

        .metric-card.pink {
            background: var(--card-pink);
        }

        .metric-label {
            font-size: clamp(1.05rem, 2vw, 1.55rem);
            line-height: 1.1;
        }

        .metric-value {
            font-size: clamp(1.45rem, 2.7vw, 2.2rem);
            line-height: 1.05;
            font-weight: 700;
        }

        .chart-card {
            background: var(--card-pink);
            min-height: 25rem;
        }

        .table-card {
            background: var(--card-teal);
        }

        .search-card {
            background: #4f8d93;
            border: 7px solid rgba(132, 185, 106, 0.95);
            min-height: 8rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff4d6;
            font-size: 2rem;
            font-weight: 800;
        }

        .search-card.compact {
            min-height: 6rem;
        }

        .item-detail-card {
            background: var(--card-orange);
            color: #fff5d0;
            border-radius: 2rem;
        }

        .item-detail-row {
            display: grid;
            grid-template-columns: 0.95fr 1.1fr;
            gap: 0.55rem;
            font-size: 1.05rem;
            margin-bottom: 0.35rem;
        }

        .item-detail-row span:first-child {
            color: #fff1ca;
            opacity: 0.95;
        }

        .item-detail-row span:last-child {
            color: #fdf5df;
        }

        .item-link a {
            color: #248ea7;
            text-decoration: underline;
            word-break: break-word;
        }

        .scroll-card {
            background: var(--sidebar);
            color: #fff3d5;
            max-height: 58vh;
            overflow-y: auto;
            border-radius: 1rem;
        }

        .score-item {
            list-style: none;
            padding: 0.38rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.12);
            font-size: 1.05rem;
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
        }

        .score-item:last-child {
            border-bottom: none;
        }

        .sidebar-brand {
            color: #fff4d2;
            font-size: 3.2rem;
            font-weight: 900;
            text-align: center;
            letter-spacing: 0.02em;
            margin: 0.65rem 0 1rem;
        }

        .sidebar-block {
            color: #fff4d2;
            font-size: 2rem;
            font-weight: 900;
            margin: 0.85rem 0 0.3rem;
        }

        /* Sidebar navigation button styling */
        section[data-testid="stSidebar"] div.stButton {
            margin: 0.1rem 0 !important;
        }

        section[data-testid="stSidebar"] div.stButton > button,
        section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            width: 100% !important;
            min-height: 3.2rem !important;
            padding: 0.4rem 1rem !important;
            border-radius: 0.95rem !important;
            border: 1px solid rgba(255, 241, 202, 0.22) !important;
            background: rgba(255, 255, 255, 0.08) !important;
            color: #fff4d2 !important;
            font-size: 2.05rem !important;
            font-weight: 900 !important;
            letter-spacing: 0.01em !important;
            line-height: 1.05 !important;
            box-shadow: none !important;
            transition: background-color 140ms ease, border-color 140ms ease !important;
        }

        section[data-testid="stSidebar"] div.stButton > button:hover,
        section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
            background: rgba(255, 255, 255, 0.16) !important;
            border-color: rgba(255, 241, 202, 0.45) !important;
        }

        section[data-testid="stSidebar"] div.stButton > button:focus,
        section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:focus {
            outline: 2px solid rgba(255, 241, 202, 0.65) !important;
            outline-offset: 2px !important;
        }

        .sidebar-list {
            margin: 0;
            padding-left: 1.3rem;
            color: #fff4d2;
            font-size: 1.6rem;
            line-height: 1.3;
        }

        .sidebar-divider {
            height: 3px;
            background: rgba(255,255,255,0.85);
            margin: 1rem 0;
        }

        .gift-box {
            margin-top: 1rem;
            border-radius: 1.4rem;
            border: 0.2rem solid rgba(255, 241, 202, 0.35);
            min-height: 10rem;
            position: relative;
            background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
        }
        /* 
        TODO: the gift is meant to be a logo for a phote, it is in canva rn and when it is doen cooking i will use it instead.
        */
        .gift-box::before {
            content: "🎁";
            position: absolute;
            inset: 0;
            display: grid;
            place-items: center;
            font-size: 6rem;
            filter: saturate(1.1);
            opacity: 0.85;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 999px;
            border: none;
            background: #f4bf68;
            color: #3b3634;
            font-weight: 800;
        }

        .stTextInput input,
        .stNumberInput input,
        .stSelectbox div[data-baseweb="select"] > div,
        .stTextArea textarea {
            background: rgba(255, 255, 255, 0.06) !important;
            color: var(--text) !important;
            border-color: rgba(255,255,255,0.14) !important;
        }

        .stDataFrame,
        .stTable {
            border-radius: 1rem;
            overflow: hidden;
        }

        .wide-gap {
            gap: 1rem;
        }

        .dashboard-grid {
            gap: 1rem;
        }

        .small-note {
            color: var(--muted);
            font-size: 0.95rem;
        }
        /* Make Streamlit input widgets visually overlap the search-card so they
           appear inside the styled card element. This keeps labels and inputs
           readable while preserving Streamlit's DOM structure. */
        .search-card {
            position: relative;
            padding-bottom: 2.6rem;
        }

        .search-card.compact {
            padding-bottom: 1.6rem;
        }

        /* Pull the immediate following Streamlit input blocks upward into the card */
        .search-card + div .stNumberInput,
        .search-card + div .stTextInput,
        .search-card.compact + div .stTextInput {
            margin-top: -2.4rem !important;
            position: relative;
            z-index: 3;
        }
        </style>
        """,
        unsafe_allow_html=True,
        # who needs seperate style sheets when you can have 3 giant files with 2000+ lines each, here i choose to take a giant dump of css
    )


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
def get_item_score_averages(db_path_str: str) -> pd.Series:
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
    st.sidebar.markdown(
        f'<div class="sidebar-brand">{APP_TITLE}</div>', unsafe_allow_html=True
    )
    # Render navigation as large, styled buttons so they are clickable
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = NAV_PAGES[0]

    # Cceate a button for each page. Pressing a button updates session state.
    for p in NAV_PAGES:
        if st.sidebar.button(p, key=f"nav_{p}"):
            st.session_state["nav_page"] = p
    # remove the dotted list; keep a divider and gift box only
    # I had a great idea to also use javascript here, i pushed that idea so deep in my arse that i forgot about it, this is the best case senario for my mental health
    st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="gift-box"></div>', unsafe_allow_html=True)
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


def render_info_pair(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="item-detail-row">
            <span>{label}</span>
            <span>{value}</span>
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
            Gyftyfy is a gift choosing assistant originally created as part of an enterprise computing assignment
            and built around SQLite-backed user profiles, item scoring, and sales reporting.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="text-align:center; margin: 0.5rem 0 1.1rem;">
            <span class="note-banner">IMPORTANT</span>
            <span class="note-line">| BEFORE USE</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.15, 1.0], gap="large")
    with left:
        st.markdown(
            """
            <div class="home-card" style="background: rgba(255,255,255,0.03); border-radius: 1.8rem; padding: 1.2rem 1.35rem; text-align:center;">
                <div style="font-size: 1.85rem; font-weight: 800; color: var(--text); line-height: 1.5;">
                    Make sure to read the README.md and the LICENSE<br>
                    Make sure to change the path for the db file in the app if you are using your own<br>
                    If you have not generated the database file yet, the app will explain what is missing
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div class="home-card" style="background: rgba(255,255,255,0.03); border-radius: 1.8rem; padding: 1.2rem 1.35rem; text-align:center; min-height: 18rem;">
                <div style="font-size: 1.6rem; font-weight: 700; color: var(--accent); line-height: 1.6;">
                    Giftyfy uses the schema tables users_login, user_profiles, items, and sales to power the
                    dashboard, item search, and table inspection views.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


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

    left_col, middle_col, right_col = st.columns([1.1, 1.55, 1.08], gap="large")
    # I love life
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
        st.markdown('<div style="height: 0.8rem"></div>', unsafe_allow_html=True)
        render_small_metric("number of sales", f"{total_sales}", tone="teal")
        st.markdown('<div style="height: 0.8rem"></div>', unsafe_allow_html=True)
        st.markdown('<div class="table-card">', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:1.1rem; font-weight:800; margin-bottom:0.45rem;">users table here</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(users_df, use_container_width=True, height=250, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        item_avg_scores = get_item_score_averages(str(db_path))
        sold_avg_scores = get_sold_item_score_averages(str(db_path))

        item_pie_df = pd.DataFrame(
            {
                "category": list(GROUPED_SCORE_FIELDS.keys()),
                "score": [
                    float(item_avg_scores[fields].mean()) if fields else 0.0
                    for fields in GROUPED_SCORE_FIELDS.values()
                ],
            }
        )
        item_pie_df["score"] = item_pie_df["score"].fillna(0.0)

        sold_pie_df = pd.DataFrame(
            {
                "category": list(GROUPED_SCORE_FIELDS.keys()),
                "score": [
                    float(sold_avg_scores[fields].mean()) if fields else 0.0
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
            color_discrete_sequence=["#4d7cf0", "#ab8ef4", "#f2bc67", "#ffd84d"],
        )
        chart1.update_layout(
            title="items score distribution",
            paper_bgcolor="#b5628e",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f7e8c2", size=13),
            margin=dict(l=10, r=10, t=44, b=10),
            showlegend=False,
            title_x=0.04,
        )
        chart1.update_traces(
            textposition="outside",
            textinfo="label+percent",
            marker=dict(line=dict(color="#b5628e", width=1)),
        )

        chart2 = px.pie(
            sold_pie_df,
            values="score",
            names="category",
            hole=0.0,
            color_discrete_sequence=["#4d7cf0", "#ab8ef4", "#f2bc67", "#ffd84d"],
        )
        chart2.update_layout(
            title="sold items score distribution",
            paper_bgcolor="#b5628e",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f7e8c2", size=13),
            margin=dict(l=10, r=10, t=44, b=10),
            showlegend=False,
            title_x=0.04,
        )
        chart2.update_traces(
            textposition="outside",
            textinfo="label+percent",
            marker=dict(line=dict(color="#b5628e", width=1)),
        )

        st.plotly_chart(
            chart1, use_container_width=True, config={"displayModeBar": False}
        )
        st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)
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
        st.markdown('<div class="search-card">', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:2rem; font-weight:800; text-align:center; padding:0.6rem 0;">user input</div>',
            unsafe_allow_html=True,
        )
        item_id = st.number_input(
            "query by ID",
            min_value=0,
            step=1,
            value=0,
            help="Enter an item_id to narrow the item search",
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

        # Compact card below for the name search and autocomplete chips
        st.markdown('<div class="search-card compact">', unsafe_allow_html=True)
        if "item_name_query" not in st.session_state:
            st.session_state["item_name_query"] = ""

        item_name_query = st.text_input(
            "query by name",
            value=st.session_state.get("item_name_query", ""),
            key="item_name_query",
            placeholder="Type to filter suggestions (autocomplete)",
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
                for _ in range((len(suggestions) + chips_per_row - 1) // chips_per_row)
            ]
            for idx, s in enumerate(suggestions):
                row = cols[idx // chips_per_row]
                col = row[idx % chips_per_row]
                if col.button(s, key=f"suggest_{idx}"):
                    st.session_state["item_name_query"] = s

        st.markdown("</div>", unsafe_allow_html=True)

        # Use the current query value (which may have been set by clicking a chip)
        item_name = st.session_state.get("item_name_query", "")

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
            st.markdown('<div class="item-detail-card">', unsafe_allow_html=True)
            render_info_pair("item ID", str(int(selected["item_id"])))
            render_info_pair("Item name", str(selected["item_name"]))
            render_info_pair("retailer", str(selected["retailer"] or ""))
            st.markdown(
                '<div class="item-detail-row"><span>associate link</span><span class="item-link">',
                unsafe_allow_html=True,
            )
            associate_link = str(selected["associate_link"] or "")
            if associate_link:
                st.markdown(
                    f"<a href='{associate_link}' target='_blank'>{associate_link}</a>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("<span>None</span>", unsafe_allow_html=True)
            st.markdown("</span></div>", unsafe_allow_html=True)
            render_info_pair(
                "price",
                f"${float(selected['price']):,.2f}"
                if pd.notna(selected["price"])
                else "",
            )
            st.markdown("</div>", unsafe_allow_html=True)
    # I will not k*** myself, I will not k*** myslef, it is only a small amout of python, 1000 lines in and i will not k*** myself.
    with right_col:
        st.markdown('<div class="scroll-card">', unsafe_allow_html=True)
        if results.empty:
            st.markdown(
                '<div style="font-size: 1.4rem; font-weight: 800; margin-bottom: 0.6rem;">score metrics</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="small-note">No item selected.</div>',
                unsafe_allow_html=True,
            )
        else:
            row = results.iloc[0]
            st.markdown(
                '<div style="font-size: 1.4rem; font-weight: 800; margin-bottom: 0.6rem;">score metrics</div>',
                unsafe_allow_html=True,
            )
            for field in SCORE_FIELDS:
                label = field.replace("_score", "").replace("_", " ").title()
                value = int(row[field]) if pd.notna(row[field]) else 0
                st.markdown(
                    f'<div class="score-item"><span>• {label}</span><span>{value}</span></div>',
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)


def render_tables_page(db_path: Path) -> None:
    st.markdown(
        '<div class="section-title" style="text-align:center; margin-bottom: 1rem;">DATABASE TABLES</div>',
        unsafe_allow_html=True,
    )

    counts = get_metric_counts(str(db_path))
    kpi_cols = st.columns(4, gap="small")
    metric_specs = [
        ("Users", counts["users_login"], "green"),
        ("Profiles", counts["user_profiles"], "teal"),
        ("Items", counts["items"], "green"),
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
        st.markdown('<div class="table-card">', unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:1.25rem; font-weight:800; margin-bottom:0.5rem;">{SCHEMA_DISPLAY_NAMES[table_name]} schema</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(schema, use_container_width=True, hide_index=True, height=300)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="table-card">', unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:1.25rem; font-weight:800; margin-bottom:0.5rem;">{SCHEMA_DISPLAY_NAMES[table_name]} preview</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(preview, use_container_width=True, hide_index=True, height=300)
        st.markdown("</div>", unsafe_allow_html=True)


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
