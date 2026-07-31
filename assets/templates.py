from typing import Any


def sidebar_brand(title: str) -> str:
    return f'<div class="sidebar-brand">{title}</div>'


def note_banner() -> str:
    return (
        '<div style="text-align:left; margin: 0.5rem 0 1.1rem;">'
        '<span class="note-banner">IMPORTANT</span>'
        '<span class="note-line">| BEFORE USE</span>'
        '</div>'
    )


def home_about_card() -> str:
    return (
        '<div class="home-card" style="background: rgba(255,255,255,0.03); border-radius: 1.8rem; padding: 1.2rem 1.35rem; text-align:center;">'
        '<div style="font-size: 1.85rem; font-weight: 800; color: var(--text); line-height: 1.5;">'
        'Make sure to read the README.md and the LICENSE<br>'
        'Make sure to change the path for the db file in the app if you are using your own<br>'
        'If you have not generated the database file yet, the app will explain what is missing'
        '</div>'
        '</div>'
    )


def home_usage_card() -> str:
    return (
        '<div class="home-card" style="background: rgba(255,255,255,0.03); border-radius: 1.8rem; padding: 1.2rem 1.35rem; text-align:center; min-height: 18rem;">'
        '<div style="font-size: 1.6rem; font-weight: 700; color: var(--accent); line-height: 1.6;">'
        'Giftyfy uses the schema tables users_login, user_profiles, items, and sales to power the'
        'dashboard, item search, and table inspection views.'
        '</div>'
        '</div>'
    )


def users_table_header() -> str:
    return '<div style="font-size:1.1rem; font-weight:800; margin-bottom:0.45rem;">users table here</div>'
