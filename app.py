# -*- coding: utf-8 -*-
"""
STRATOS - Strategic Intelligence Platform
Version complete : Streamlit + SQLite

Lancement :  streamlit run app.py
Dependances : streamlit pandas requests plotly
"""

import html
import io
import os
import re
import sqlite3
import xml.etree.ElementTree as ET
from contextlib import closing
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import requests
import streamlit as st

# ==================================================
# 0. CONFIGURATION
# ==================================================

DB_PATH = "stratos.db"

# --------------------------------------------------
# PERSONNALISATION : modifiez uniquement ces 4 lignes
# --------------------------------------------------
OWNER_NAME = "NTE Alan Gabriel"
OWNER_TITLE = "Analyste en intelligence économique"
ORG_NAME = "Meridian Risk Advisory"
LOGO_PATH = "logo.png"  # facultatif : image placée à côté de app.py

st.set_page_config(
    page_title=f"STRATOS | {ORG_NAME}", page_icon="🌐", layout="wide"
)

REGIONS = [
    "Afrique du Nord",
    "Afrique de l'Ouest",
    "Afrique centrale",
    "Afrique de l'Est",
    "Afrique australe",
    "Europe",
    "Amérique du Nord",
    "Asie-Pacifique",
    "Autre",
]

SECTEURS = [
    "Énergie et infrastructures",
    "Finance et banque",
    "Mines et ressources naturelles",
    "Agriculture",
    "Télécommunications",
    "Industrie",
    "Commerce",
    "Géopolitique",
    "Réglementation",
    "Autre",
]

IMPORTANCES = ["Faible", "Moyenne", "Élevée", "Critique"]
MENACES = ["Faible", "Moyenne", "Élevée"]


# ==================================================
# THEME VISUEL HIGH-TECH
# ==================================================

ACCENTS = {
    "cyan": "#3B82F6",
    "violet": "#94A3B8",
    "green": "#22C55E",
    "amber": "#F59E0B",
    "red": "#EF4444",
}
CYBER_SCALE = [[0.0, "#93C5FD"], [0.5, "#F59E0B"], [1.0, "#EF4444"]]
CYBER_COLORWAY = [
    "#3B82F6", "#22C55E", "#F59E0B", "#EF4444", "#94A3B8", "#A855F7",
]

THEME_CSS = """<style>
html, body, [class*="css"], .stApp { font-family: Arial, Helvetica, sans-serif; }
.stApp { background: #0F172A; color: #E2E8F0; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.4rem; max-width: 1500px; }
h1, h2, h3 { font-family: Arial, Helvetica, sans-serif !important; font-weight: 700; color: #F8FAFC; }
h2 { border-left: 4px solid #3B82F6; padding-left: 12px; }
[data-testid="stSidebar"] { background: #0B1220; border-right: 1px solid #1E293B; }
[data-testid="stSidebar"] .stRadio label { padding: 6px 4px; border-radius: 6px; }
[data-testid="stSidebar"] .stRadio label:hover { background: #1E293B; }
[data-testid="stMetric"] { background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 12px 14px; }
[data-testid="stMetricValue"] { color: #F8FAFC; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #334155; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 6px 6px 0 0; padding: 8px 16px; }
.stTabs [aria-selected="true"] { color: #3B82F6; border-bottom: 2px solid #3B82F6; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  background: #2563EB; border: 1px solid #2563EB; color: #FFFFFF; border-radius: 6px;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  background: #1D4ED8; border-color: #1D4ED8; color: #FFFFFF;
}
[data-testid="stExpander"] { border: 1px solid #334155; border-radius: 8px; background: #111C30; }
[data-testid="stDataFrame"] { border: 1px solid #334155; border-radius: 8px; overflow: hidden; }
.topbar { display:flex; justify-content:space-between; align-items:center; padding: 10px 18px; margin-bottom: 14px;
  border: 1px solid #334155; border-radius: 8px; background: #1E293B; }
.brand { font-weight:700; font-size:1.25rem; letter-spacing:.08em; color:#F8FAFC; }
.brand span { font-weight:400; font-size:.7rem; letter-spacing:.1em; color:#94A3B8; margin-left:14px; }
.status { font-size:.75rem; color:#94A3B8; }
.dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#22C55E; margin-right:8px; }
.kpi { --a:#3B82F6; padding:14px 16px; border-radius:8px; background:#1E293B;
  border:1px solid #334155; border-top:3px solid var(--a); }
.kpi-label { font-size:.7rem; letter-spacing:.08em; text-transform:uppercase; color:#94A3B8; }
.kpi-value { font-size:1.7rem; font-weight:700; color:var(--a); margin:4px 0; }
.kpi-sub { font-size:.72rem; color:#94A3B8; }
.sec { font-size:.85rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  color:#CBD5E1; margin:18px 0 10px; display:flex; align-items:center; gap:10px; }
.sec::after { content:''; flex:1; height:1px; background:#334155; }
.live { font-size:.62rem; letter-spacing:.1em; padding:2px 8px; border-radius:999px; color:#22C55E;
  border:1px solid #22C55E; }
.chips { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:6px; }
.chip { display:flex; gap:8px; align-items:baseline; padding:6px 12px; border-radius:6px;
  background:#1E293B; border:1px solid #334155; font-size:.78rem; color:#94A3B8; }
.chip b { color:#F8FAFC; font-weight:700; }
.news-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:10px; }
a.news { display:block; text-decoration:none; padding:12px 14px; border-radius:8px; background:#1E293B;
  border:1px solid #334155; border-left:3px solid #3B82F6; }
a.news:hover { background:#243247; }
.news-title { color:#E2E8F0; font-size:.88rem; font-weight:600; line-height:1.35; }
.news-meta { color:#94A3B8; font-size:.7rem; margin-top:6px; }
</style>"""


def inject_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def build_plotly_template():
    tpl = go.layout.Template(pio.templates["plotly_dark"])
    grid = "rgba(148,163,184,.18)"
    tpl.layout.update(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=CYBER_COLORWAY,
        font=dict(family="Arial, Helvetica, sans-serif", color="#CBD5E1"),
        xaxis=dict(gridcolor=grid, zerolinecolor=grid),
        yaxis=dict(gridcolor=grid, zerolinecolor=grid),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#0F172A", bordercolor="#3B82F6"),
    )
    pio.templates["stratos"] = tpl
    pio.templates.default = "stratos"


def style_geo(fig, height=520):
    fig.update_geos(
        bgcolor="rgba(0,0,0,0)",
        showland=True,
        landcolor="#1E293B",
        showocean=True,
        oceancolor="#0F172A",
        showlakes=True,
        lakecolor="#0F172A",
        showcountries=True,
        countrycolor="#475569",
        showcoastlines=True,
        coastlinecolor="#64748B",
        showframe=False,
        projection_type="natural earth",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=40, b=0),
        height=height,
    )
    return fig


def esc(value):
    return html.escape(str(value), quote=True)


def kpi_card(label, value, sub="", accent="cyan"):
    return (
        f'<div class="kpi" style="--a:{ACCENTS[accent]}">'
        f'<div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-value">{esc(value)}</div>'
        f'<div class="kpi-sub">{esc(sub)}</div></div>'
    )


def chip(label, value):
    return f'<div class="chip"><span>{esc(label)}</span><b>{esc(value)}</b></div>'


def news_card(item):
    return (
        f'<a class="news" href="{esc(item["lien"])}" target="_blank" '
        f'rel="noopener noreferrer">'
        f'<div class="news-title">{esc(item["titre"])}</div>'
        f'<div class="news-meta">{esc(item["source"])} · {esc(item["date"])}</div>'
        f'</a>'
    )


def section_title(text, live=False):
    badge = '<span class="live">● LIVE</span>' if live else ""
    return f'<div class="sec">{esc(text)}{badge}</div>'


build_plotly_template()
inject_theme()


# ==================================================
# 1. OUTILS D'AFFICHAGE (compatibles anciennes/nouvelles versions)
# ==================================================

def show_df(df, **kwargs):
    """Affiche un tableau pleine largeur."""
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True, **kwargs)


def show_chart(fig):
    """Affiche un graphique Plotly pleine largeur avec le thème STRATOS."""
    try:
        st.plotly_chart(fig, width="stretch", theme=None)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, theme=None)


# ==================================================
# 2. BASE DE DONNEES
# ==================================================

def run_query(sql, params=()):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def run_exec(sql, params=()):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(sql, params)
        conn.commit()


def run_exec_many(sql, rows):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.executemany(sql, rows)
        conn.commit()


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS intelligence_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_ajout TEXT NOT NULL,
                titre TEXT NOT NULL,
                source TEXT,
                lien TEXT,
                region TEXT,
                secteur TEXT,
                resume TEXT NOT NULL,
                importance TEXT
            )
            """
        )
        # Migrations : colonnes ajoutees apres la premiere version
        existing = {
            row[1]
            for row in conn.execute("PRAGMA table_info(intelligence_items)")
        }
        if "pays" not in existing:
            conn.execute("ALTER TABLE intelligence_items ADD COLUMN pays TEXT")
        if "origine" not in existing:
            conn.execute(
                "ALTER TABLE intelligence_items "
                "ADD COLUMN origine TEXT DEFAULT 'Manuelle'"
            )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_ajout TEXT NOT NULL,
                nom TEXT NOT NULL,
                secteur TEXT,
                pays TEXT,
                site TEXT,
                forces TEXT,
                faiblesses TEXT,
                risques TEXT,
                menace TEXT,
                notes TEXT
            )
            """
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS app_flags "
            "(key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS financial_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise TEXT NOT NULL,
                periode TEXT NOT NULL,
                ca REAL, ebit REAL, resultat_net REAL,
                total_actifs REAL, capitaux_propres REAL,
                dette REAL, taux_impot REAL,
                UNIQUE (entreprise, periode)
            )
            """
        )
        conn.commit()


init_db()


# ==================================================
# 3. DONNEES BANQUE MONDIALE (avec cache)
# ==================================================

COUNTRIES = {
    "France": "FRA",
    "Allemagne": "DEU",
    "États-Unis": "USA",
    "Japon": "JPN",
    "Maroc": "MAR",
    "Cameroun": "CMR",
    "Côte d'Ivoire": "CIV",
    "Sénégal": "SEN",
    "Afrique du Sud": "ZAF",
    "Nigeria": "NGA",
    "Kenya": "KEN",
    "Ghana": "GHA",
    "Égypte": "EGY",
    "RD Congo": "COD",
    "Éthiopie": "ETH",
}

WB_INDICATORS = {
    "Croissance du PIB (%)": "NY.GDP.MKTP.KD.ZG",
    "Inflation annuelle (%)": "FP.CPI.TOTL.ZG",
    "Chômage (%)": "SL.UEM.TOTL.ZS",
    "Dette extérieure (% du RNB)": "DT.DOD.DECT.GN.ZS",
    "PIB par habitant (USD courants)": "NY.GDP.PCAP.CD",
    "Population totale": "SP.POP.TOTL",
    "IDE nets (% du PIB)": "BX.KLT.DINV.WD.GD.ZS",
    "Accès à l'électricité (%)": "EG.ELC.ACCS.ZS",
}

MAP_INDICATORS = {
    "Croissance du PIB (%)": "NY.GDP.MKTP.KD.ZG",
    "Inflation (%)": "FP.CPI.TOTL.ZG",
    "Chômage (%)": "SL.UEM.TOTL.ZS",
    "Population": "SP.POP.TOTL",
    "PIB par habitant (USD courants)": "NY.GDP.PCAP.CD",
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_wb_series(country_code, indicator_code, start_year, end_year):
    url = (
        "https://api.worldbank.org/v2/country/"
        f"{country_code}/indicator/{indicator_code}"
    )
    params = {
        "format": "json",
        "per_page": 100,
        "date": f"{start_year}:{end_year}",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    result = response.json()

    if (
        not isinstance(result, list)
        or len(result) < 2
        or not isinstance(result[1], list)
    ):
        return pd.DataFrame(columns=["Année", "Valeur"])

    records = []
    for obs in result[1]:
        value = obs.get("value")
        year = obs.get("date")
        if value is not None and year is not None:
            records.append({"Année": int(year), "Valeur": float(value)})

    df = pd.DataFrame(records, columns=["Année", "Valeur"])
    if df.empty:
        return df
    return (
        df.drop_duplicates(subset=["Année"])
        .sort_values("Année")
        .reset_index(drop=True)
    )


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_wb_world(indicator_code, year):
    url = (
        "https://api.worldbank.org/v2/country/all/indicator/"
        f"{indicator_code}"
    )
    params = {"format": "json", "date": str(year), "per_page": 20000}
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    result = response.json()

    if (
        not isinstance(result, list)
        or len(result) < 2
        or not isinstance(result[1], list)
    ):
        return pd.DataFrame(columns=["Pays", "Code", "Valeur"])

    records = []
    for obs in result[1]:
        value = obs.get("value")
        iso3 = obs.get("countryiso3code")
        name = (obs.get("country") or {}).get("value")
        if value is not None and iso3 and name:
            records.append(
                {"Pays": name, "Code": iso3, "Valeur": float(value)}
            )

    df = pd.DataFrame(records, columns=["Pays", "Code", "Valeur"])
    return df.drop_duplicates(subset=["Code"]) if not df.empty else df


# ==================================================
# DONNEES EN DIRECT (sources ouvertes, sans cle API)
# ==================================================

HTTP_HEADERS = {"User-Agent": "STRATOS/2.0 (strategic intelligence)"}

NEWS_THEMES = {
    "Afrique — investissements & économie": "Afrique investissement économie",
    "Énergie & infrastructures (Afrique)": "Afrique énergie infrastructures projet",
    "Mines & ressources (Afrique)": "Afrique mines ressources naturelles",
    "Risque pays & géopolitique": "risque pays géopolitique Afrique",
    "Finance & banque (Afrique)": "Afrique banque finance FMI Banque mondiale",
    "Télécoms & numérique (Afrique)": "Afrique télécommunications numérique",
}

FX_FOCUS = [
    "USD", "GBP", "JPY", "CNY", "MAD", "XOF",
    "XAF", "NGN", "ZAR", "EGP", "KES", "GHS",
]

QUAKE_FEEDS = {
    "M4.5+ — 7 derniers jours": "4.5_week",
    "M2.5+ — dernières 24 h": "2.5_day",
}


@st.cache_data(ttl=900, show_spinner=False)
def fetch_news(query, hl="fr", gl="FR", limit=20):
    """Actualités réelles via le flux RSS de Google Actualités."""
    response = requests.get(
        "https://news.google.com/rss/search",
        params={"q": f"{query} when:7d", "hl": hl, "gl": gl,
                "ceid": f"{gl}:{hl}"},
        timeout=15,
        headers=HTTP_HEADERS,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)

    articles = []
    for item in root.iter("item"):
        title = clean_html(item.findtext("title"))
        source = clean_html(item.findtext("source"))
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3]
        try:
            moment = parsedate_to_datetime(item.findtext("pubDate"))
        except (TypeError, ValueError):
            moment = None
        articles.append(
            {
                "titre": title,
                "source": source or "Google Actualités",
                "lien": (item.findtext("link") or "").strip(),
                "date": moment.strftime("%Y-%m-%d %H:%M") if moment else "",
                "ts": moment.timestamp() if moment else 0,
            }
        )

    articles = [a for a in articles if a["titre"] and a["lien"]]
    articles.sort(key=lambda a: a["ts"], reverse=True)
    return articles[:limit]


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fx():
    """Taux de change réels (base EUR) via open.er-api.com."""
    response = requests.get(
        "https://open.er-api.com/v6/latest/EUR",
        timeout=10,
        headers=HTTP_HEADERS,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("result") != "success":
        raise ValueError("Réponse inattendue du service de taux de change.")
    return {
        "rates": data["rates"],
        "updated": data.get("time_last_update_utc", ""),
    }


@st.cache_data(ttl=600, show_spinner=False)
def fetch_quakes(feed):
    """Séismes réels (USGS) : indicateur de risque naturel."""
    url = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/"
        f"{feed}.geojson"
    )
    response = requests.get(url, timeout=20, headers=HTTP_HEADERS)
    response.raise_for_status()
    features = response.json().get("features", [])

    rows = []
    for feat in features:
        props = feat.get("properties", {})
        coords = (feat.get("geometry") or {}).get("coordinates") or [None] * 3
        if props.get("mag") is None or coords[0] is None:
            continue
        moment = datetime.fromtimestamp(
            props["time"] / 1000, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M")
        rows.append(
            {
                "Date (UTC)": moment,
                "Magnitude": float(props["mag"]),
                "Lieu": props.get("place") or "n/a",
                "Profondeur (km)": coords[2],
                "Lat": coords[1],
                "Lon": coords[0],
                "Détail": props.get("url") or "",
            }
        )
    df = pd.DataFrame(
        rows,
        columns=["Date (UTC)", "Magnitude", "Lieu", "Profondeur (km)",
                 "Lat", "Lon", "Détail"],
    )
    return df.sort_values("Date (UTC)", ascending=False).reset_index(drop=True)


def save_articles(df, region, secteur, importance, origine):
    """Enregistre des articles sélectionnés dans l'Intelligence Feed."""
    known = set(
        run_query("SELECT lien FROM intelligence_items")["lien"].dropna()
    )
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []
    for _, art in df.iterrows():
        if art["lien"] in known:
            continue
        rows.append(
            (
                now,
                art["titre"],
                art["source"],
                art["lien"],
                region,
                secteur,
                f"{art['titre']} ({art['source']}, {art['date']})",
                importance,
                "",
                origine,
            )
        )
    if rows:
        run_exec_many(
            """
            INSERT INTO intelligence_items
            (date_ajout, titre, source, lien, region, secteur,
             resume, importance, pays, origine)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    return len(rows)


# ==================================================
# LIVE MONITOR
# ==================================================

def live_tab_news():
    c1, c2, c3 = st.columns([2, 2, 1])
    theme = c1.selectbox("Thème", list(NEWS_THEMES.keys()), key="live_theme")
    custom = c2.text_input(
        "…ou votre propre requête",
        key="live_custom",
        placeholder="Ex. : Cameroun port Kribi investissement",
    )
    lang = c3.selectbox("Langue", ["Français", "English"], key="live_lang")

    query = custom.strip() or NEWS_THEMES[theme]
    hl, gl = ("fr", "FR") if lang == "Français" else ("en", "US")

    try:
        with st.spinner("Collecte des actualités en direct..."):
            articles = fetch_news(query, hl, gl, 20)
    except (requests.RequestException, ET.ParseError) as error:
        st.error(f"Flux d'actualités indisponible : {error}")
        return

    if not articles:
        st.info("Aucun article trouvé pour cette requête.")
        return

    st.caption(
        f"{len(articles)} articles · requête « {query} » · 7 derniers jours "
        "· source : Google Actualités (titres et liens vers les éditeurs)."
    )
    cards = "".join(news_card(a) for a in articles[:12])
    st.markdown(f'<div class="news-grid">{cards}</div>', unsafe_allow_html=True)

    with st.expander("📥 Importer des articles dans l'Intelligence Feed"):
        df = pd.DataFrame(articles)[["titre", "source", "date", "lien"]]
        df.insert(0, "Importer", False)
        edited = st.data_editor(
            df,
            hide_index=True,
            key=f"live_import_{abs(hash(query))}",
            column_config={
                "Importer": st.column_config.CheckboxColumn("Importer"),
                "titre": st.column_config.TextColumn("Titre", disabled=True),
                "source": st.column_config.TextColumn("Source", disabled=True),
                "date": st.column_config.TextColumn("Date", disabled=True),
                "lien": st.column_config.LinkColumn("Lien", disabled=True),
            },
        )
        k1, k2, k3 = st.columns(3)
        region = k1.selectbox("Région", REGIONS, key="live_imp_region")
        secteur = k2.selectbox("Secteur", SECTEURS, key="live_imp_sector")
        importance = k3.selectbox(
            "Importance", IMPORTANCES, index=1, key="live_imp_level"
        )
        if st.button("Importer la sélection", type="primary", key="live_imp_btn"):
            selected = edited[edited["Importer"]]
            if selected.empty:
                st.warning("Aucun article sélectionné.")
            else:
                n = save_articles(
                    selected, region, secteur, importance, "Google Actualités"
                )
                st.success(f"{n} article(s) importé(s) (doublons ignorés).")


def live_tab_fx():
    try:
        with st.spinner("Chargement des taux de change..."):
            fx = fetch_fx()
    except (requests.RequestException, ValueError) as error:
        st.error(f"Service de taux de change indisponible : {error}")
        return

    rates = fx["rates"]
    chips = "".join(
        chip(f"1 EUR → {code}", f"{rates[code]:,.4f}")
        for code in FX_FOCUS
        if code in rates
    )
    st.markdown(f'<div class="chips">{chips}</div>', unsafe_allow_html=True)
    st.caption(
        f"Taux indicatifs — source : open.er-api.com — mise à jour : "
        f"{fx['updated'] or 'n/a'}. Ne pas utiliser pour une transaction."
    )

    st.markdown(section_title("Convertisseur"), unsafe_allow_html=True)
    codes = ["EUR"] + sorted(c for c in rates if c != "EUR")
    c1, c2, c3 = st.columns(3)
    amount = c1.number_input("Montant", min_value=0.0, value=1000.0)
    src = c2.selectbox("De", codes, index=0, key="fx_from")
    dst_default = codes.index("XOF") if "XOF" in codes else 1
    dst = c3.selectbox("Vers", codes, index=dst_default, key="fx_to")

    rate_src = 1.0 if src == "EUR" else rates[src]
    rate_dst = 1.0 if dst == "EUR" else rates[dst]
    converted = amount / rate_src * rate_dst
    st.metric(f"{amount:,.2f} {src} =", f"{converted:,.2f} {dst}")


def live_tab_quakes():
    label = st.selectbox("Période / seuil", list(QUAKE_FEEDS.keys()))
    try:
        with st.spinner("Lecture du flux sismique USGS..."):
            df = fetch_quakes(QUAKE_FEEDS[label])
    except requests.RequestException as error:
        st.error(f"Flux USGS indisponible : {error}")
        return

    if df.empty:
        st.info("Aucun séisme sur cette période.")
        return

    c1, c2, c3 = st.columns(3)
    c1.markdown(
        kpi_card("Événements", len(df), "sur la période", "cyan"),
        unsafe_allow_html=True,
    )
    c2.markdown(
        kpi_card("Magnitude max", f"{df['Magnitude'].max():.1f}", "échelle ouverte", "red"),
        unsafe_allow_html=True,
    )
    c3.markdown(
        kpi_card("Profondeur moyenne", f"{df['Profondeur (km)'].mean():.0f} km", "", "violet"),
        unsafe_allow_html=True,
    )

    fig = px.scatter_geo(
        df,
        lat="Lat",
        lon="Lon",
        size="Magnitude",
        color="Magnitude",
        hover_name="Lieu",
        hover_data={"Date (UTC)": True, "Magnitude": ":.1f",
                    "Lat": False, "Lon": False},
        color_continuous_scale=CYBER_SCALE,
        size_max=18,
        title="Activité sismique mondiale",
    )
    style_geo(fig)
    show_chart(fig)

    with st.expander("Tableau des événements"):
        show_df(
            df.drop(columns=["Lat", "Lon"]),
            column_config={
                "Détail": st.column_config.LinkColumn(
                    "Détail", display_text="USGS"
                )
            },
        )
    st.caption(
        "Source : USGS Earthquake Hazards Program. Données réelles, "
        "mises à jour en continu. Utile pour le suivi des risques "
        "naturels sur les actifs et infrastructures."
    )


def live_tab_country():
    country = st.selectbox("Pays", list(COUNTRIES.keys()), key="live_country")
    code = COUNTRIES[country]

    snapshot = [
        ("Croissance du PIB", "NY.GDP.MKTP.KD.ZG", "%", "cyan"),
        ("Inflation", "FP.CPI.TOTL.ZG", "%", "amber"),
        ("Chômage", "SL.UEM.TOTL.ZS", "%", "violet"),
        ("PIB / habitant", "NY.GDP.PCAP.CD", "USD", "green"),
        ("IDE nets (% PIB)", "BX.KLT.DINV.WD.GD.ZS", "%", "cyan"),
        ("Accès électricité", "EG.ELC.ACCS.ZS", "%", "amber"),
        ("Population", "SP.POP.TOTL", "", "violet"),
        ("Dette ext. (% RNB)", "DT.DOD.DECT.GN.ZS", "%", "red"),
    ]

    this_year = datetime.now().year
    cards = []
    try:
        with st.spinner("Interrogation de la Banque mondiale..."):
            for label, ind, unit, accent in snapshot:
                df = fetch_wb_series(code, ind, this_year - 10, this_year)
                if df.empty:
                    cards.append(kpi_card(label, "n/d", "non disponible", accent))
                    continue
                last = df.iloc[-1]
                value = last["Valeur"]
                if unit == "%":
                    text = f"{value:.1f} %"
                elif unit == "USD":
                    text = f"{value:,.0f} $"
                else:
                    text = f"{value:,.0f}"
                cards.append(
                    kpi_card(label, text, f"dernière donnée : {int(last['Année'])}", accent)
                )
    except requests.RequestException as error:
        st.error(f"Banque mondiale indisponible : {error}")
        return

    for start in range(0, len(cards), 4):
        cols = st.columns(4)
        for col, card in zip(cols, cards[start:start + 4]):
            col.markdown(card, unsafe_allow_html=True)

    st.caption(
        "Valeurs réelles de la Banque mondiale (dernière année disponible "
        "pour chaque indicateur — les années peuvent différer)."
    )

    st.markdown(section_title(f"Actualités — {country}", live=True),
                unsafe_allow_html=True)
    try:
        news = fetch_news(f"{country} économie investissement", "fr", "FR", 8)
    except (requests.RequestException, ET.ParseError):
        st.info("Flux d'actualités indisponible pour le moment.")
        return
    cards_html = "".join(news_card(a) for a in news)
    st.markdown(f'<div class="news-grid">{cards_html}</div>',
                unsafe_allow_html=True)


def page_live_monitor():
    st.header("📡 Live Monitor")
    st.write(
        "Données réelles en direct : actualités, taux de change, activité "
        "sismique et fiches pays. Chaque donnée indique sa source."
    )
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📰 Actualités", "💱 Devises", "🌋 Risques naturels", "🪪 Fiche pays"]
    )
    with tab1:
        live_tab_news()
    with tab2:
        live_tab_fx()
    with tab3:
        live_tab_quakes()
    with tab4:
        live_tab_country()


# ==================================================
# DASHBOARD
# ==================================================

def page_dashboard():
    st.markdown(
        f'<div style="font-size:.65rem;color:#64748B;letter-spacing:.08em;'
        f'margin:0 0 8px;">Session de {esc(OWNER_NAME)}</div>',
        unsafe_allow_html=True,
    )
    items = run_query("SELECT * FROM intelligence_items")
    competitors = run_query("SELECT * FROM competitors")

    nb_items = len(items)
    nb_alerts = (
        int(items["importance"].isin(["Élevée", "Critique", "Elevee"]).sum())
        if nb_items else 0
    )
    nb_sources = (
        items["source"].replace("", np.nan).dropna().nunique()
        if nb_items else 0
    )

    # ---- KPI internes ----
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Informations", nb_items, "base STRATOS", "cyan"),
                unsafe_allow_html=True)
    c2.markdown(kpi_card("Sources distinctes", nb_sources, "veille", "violet"),
                unsafe_allow_html=True)
    c3.markdown(kpi_card("Alertes", nb_alerts, "élevée / critique", "red"),
                unsafe_allow_html=True)
    c4.markdown(kpi_card("Entreprises suivies", len(competitors), "registre", "green"),
                unsafe_allow_html=True)

    # ---- Bandeau devises ----
    st.markdown(section_title("Marchés des changes", live=True),
                unsafe_allow_html=True)
    try:
        fx = fetch_fx()
        chips = "".join(
            chip(f"EUR/{code}", f"{fx['rates'][code]:,.3f}")
            for code in FX_FOCUS if code in fx["rates"]
        )
        st.markdown(f'<div class="chips">{chips}</div>', unsafe_allow_html=True)
    except (requests.RequestException, ValueError):
        st.caption("Taux de change indisponibles pour le moment.")

    # ---- Actualités + séismes ----
    left, right = st.columns([3, 2])

    with left:
        st.markdown(section_title("Actualités stratégiques", live=True),
                    unsafe_allow_html=True)
        try:
            news = fetch_news(NEWS_THEMES["Afrique — investissements & économie"],
                              "fr", "FR", 8)
            st.markdown(
                '<div class="news-grid" style="grid-template-columns:1fr;">'
                + "".join(news_card(a) for a in news[:6])
                + "</div>",
                unsafe_allow_html=True,
            )
        except (requests.RequestException, ET.ParseError):
            st.caption("Flux d'actualités indisponible pour le moment.")

    with right:
        st.markdown(section_title("Activité sismique (7 j)", live=True),
                    unsafe_allow_html=True)
        try:
            quakes = fetch_quakes("4.5_week")
            if quakes.empty:
                st.caption("Aucun séisme M4.5+ sur 7 jours.")
            else:
                fig = px.scatter_geo(
                    quakes, lat="Lat", lon="Lon", size="Magnitude",
                    color="Magnitude", hover_name="Lieu",
                    color_continuous_scale=CYBER_SCALE, size_max=14,
                )
                style_geo(fig, height=340)
                fig.update_layout(coloraxis_showscale=False)
                show_chart(fig)
        except requests.RequestException:
            st.caption("Flux sismique indisponible pour le moment.")

    st.caption(
        "Sources en direct : Google Actualités, open.er-api.com, USGS. "
        "Détail et import dans le module Live Monitor."
    )

    # ---- Données internes ----
    st.markdown(section_title("Votre veille interne"), unsafe_allow_html=True)

    if not nb_items:
        st.info(
            "Aucune information enregistrée. Ajoutez-en dans l'Intelligence "
            "Feed ou importez des actualités depuis le Live Monitor."
        )
        return

    a, b = st.columns(2)
    with a:
        by_region = (
            items["region"].fillna("Non renseignée").value_counts().reset_index()
        )
        by_region.columns = ["Région", "Nombre"]
        show_chart(px.bar(by_region, x="Région", y="Nombre",
                          title="Informations par région"))
    with b:
        by_imp = (
            items["importance"].fillna("Non renseignée").value_counts().reset_index()
        )
        by_imp.columns = ["Importance", "Nombre"]
        show_chart(px.pie(by_imp, names="Importance", values="Nombre",
                          hole=0.55, title="Importance stratégique"))

    alerts = items[
        items["importance"].isin(["Élevée", "Critique", "Elevee"])
    ].sort_values("id", ascending=False).head(5)
    if not alerts.empty:
        st.markdown(section_title("Dernières alertes"), unsafe_allow_html=True)
        for _, row in alerts.iterrows():
            st.warning(
                f"**{row['titre']}** ({row['importance']}) — "
                f"{row['region'] or 'Région n/a'} | "
                f"{row['secteur'] or 'Secteur n/a'} | {row['date_ajout']}"
            )


# ==================================================
# 5. INTELLIGENCE FEED
# ==================================================

def clean_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def fetch_rss(url):
    """Lit un flux RSS/Atom simple et retourne une liste d'articles."""
    response = requests.get(
        url, timeout=30, headers={"User-Agent": "STRATOS/1.0"}
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)

    articles = []

    # RSS 2.0
    for item in root.iter("item"):
        articles.append(
            {
                "titre": clean_html(item.findtext("title")),
                "lien": (item.findtext("link") or "").strip(),
                "resume": clean_html(item.findtext("description"))[:600],
                "date": (item.findtext("pubDate") or "").strip(),
            }
        )

    # Atom
    if not articles:
        ns = "{http://www.w3.org/2005/Atom}"
        for entry in root.iter(ns + "entry"):
            link_el = entry.find(ns + "link")
            link = link_el.get("href", "") if link_el is not None else ""
            summary = entry.findtext(ns + "summary") or entry.findtext(
                ns + "content"
            )
            articles.append(
                {
                    "titre": clean_html(entry.findtext(ns + "title")),
                    "lien": link.strip(),
                    "resume": clean_html(summary)[:600],
                    "date": (entry.findtext(ns + "updated") or "").strip(),
                }
            )

    return [a for a in articles if a["titre"]]


def feed_add_form():
    st.subheader("Ajouter une information")

    with st.form("intelligence_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            title = st.text_input(
                "Titre de l'information *",
                placeholder="Ex. : Annonce d'un investissement énergétique",
            )
            source = st.text_input(
                "Source",
                placeholder="Ex. : Banque mondiale, presse, institution",
            )
            url = st.text_input(
                "Lien vers la source (facultatif)", placeholder="https://..."
            )
            pays = st.text_input("Pays concerné (facultatif)")
        with c2:
            region = st.selectbox("Région", REGIONS)
            sector = st.selectbox("Secteur", SECTEURS)
            importance = st.selectbox("Importance stratégique", IMPORTANCES)

        summary = st.text_area(
            "Résumé de l'information *",
            placeholder="Quels sont les faits importants ?",
        )
        submitted = st.form_submit_button("Enregistrer l'information")

    if submitted:
        if not title.strip() or not summary.strip():
            st.warning("Le titre et le résumé sont obligatoires.")
        else:
            run_exec(
                """
                INSERT INTO intelligence_items
                (date_ajout, titre, source, lien, region, secteur,
                 resume, importance, pays, origine)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Manuelle')
                """,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    title.strip(),
                    source.strip(),
                    url.strip(),
                    region,
                    sector,
                    summary.strip(),
                    importance,
                    pays.strip(),
                ),
            )
            st.success("Information enregistrée durablement dans STRATOS.")


def feed_rss_import():
    st.subheader("Import depuis un flux RSS / Atom")
    st.caption(
        "Préparation à la veille automatisée : collez l'adresse d'un flux "
        "RSS (presse, institution, agence) et choisissez les articles à "
        "importer. Les articles importés sont marqués « RSS »."
    )

    rss_url = st.text_input("Adresse du flux RSS", key="rss_url")
    c1, c2, c3 = st.columns(3)
    rss_region = c1.selectbox("Région par défaut", REGIONS, key="rss_region")
    rss_sector = c2.selectbox("Secteur par défaut", SECTEURS, key="rss_sector")
    rss_importance = c3.selectbox(
        "Importance par défaut", IMPORTANCES, index=1, key="rss_importance"
    )

    if st.button("Lire le flux", key="rss_read"):
        if not rss_url.strip():
            st.warning("Veuillez saisir l'adresse d'un flux.")
        else:
            try:
                with st.spinner("Lecture du flux..."):
                    st.session_state["rss_articles"] = fetch_rss(
                        rss_url.strip()
                    )
                    st.session_state["rss_source"] = rss_url.strip()
            except (requests.RequestException, ET.ParseError) as error:
                st.error(f"Impossible de lire le flux : {error}")

    articles = st.session_state.get("rss_articles", [])
    if not articles:
        return

    df = pd.DataFrame(articles)
    df.insert(0, "Importer", False)

    edited = st.data_editor(
        df,
        hide_index=True,
        key="rss_editor",
        column_config={
            "Importer": st.column_config.CheckboxColumn("Importer"),
            "titre": st.column_config.TextColumn("Titre", disabled=True),
            "lien": st.column_config.LinkColumn("Lien", disabled=True),
            "resume": st.column_config.TextColumn("Résumé", disabled=True),
            "date": st.column_config.TextColumn("Date", disabled=True),
        },
    )

    if st.button("Importer la sélection", type="primary", key="rss_import"):
        selected = edited[edited["Importer"]]
        if selected.empty:
            st.warning("Aucun article sélectionné.")
            return

        known_links = set(
            run_query("SELECT lien FROM intelligence_items")["lien"].dropna()
        )
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        rows = []
        for _, art in selected.iterrows():
            if art["lien"] and art["lien"] in known_links:
                continue
            rows.append(
                (
                    now,
                    art["titre"],
                    st.session_state.get("rss_source", "RSS"),
                    art["lien"],
                    rss_region,
                    rss_sector,
                    art["resume"] or art["titre"],
                    rss_importance,
                    "",
                    "RSS",
                )
            )

        if rows:
            run_exec_many(
                """
                INSERT INTO intelligence_items
                (date_ajout, titre, source, lien, region, secteur,
                 resume, importance, pays, origine)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            st.success(f"{len(rows)} article(s) importé(s).")
        else:
            st.info("Ces articles sont déjà présents dans la base.")


def feed_list():
    st.subheader("Informations collectées")

    items = run_query(
        """
        SELECT id, date_ajout, titre, source, lien, pays, region, secteur,
               resume, importance, COALESCE(origine, 'Manuelle') AS origine
        FROM intelligence_items
        ORDER BY id DESC
        """
    )

    if items.empty:
        st.info(
            "Aucune information ajoutée pour le moment. "
            "Utilisez le formulaire ci-dessus."
        )
        return

    # ---- Filtres ----
    search = st.text_input(
        "🔎 Recherche (titre, source, pays, région, résumé)", key="feed_search"
    )

    c1, c2, c3 = st.columns(3)
    sel_regions = c1.multiselect("Région", REGIONS, key="feed_regions")
    sel_sectors = c2.multiselect("Secteur", SECTEURS, key="feed_sectors")
    sel_imp = c3.multiselect(
        "Importance", IMPORTANCES, default=IMPORTANCES, key="feed_imp"
    )

    items["_date"] = pd.to_datetime(items["date_ajout"], errors="coerce")
    valid_dates = items["_date"].dropna()

    date_range = None
    if not valid_dates.empty:
        dmin = valid_dates.min().date()
        dmax = valid_dates.max().date()
        date_range = st.date_input(
            "Période (date d'ajout)",
            value=(dmin, dmax),
            min_value=dmin,
            max_value=max(dmax, datetime.now().date()),
            key="feed_dates",
        )

    df = items.copy()

    if search.strip():
        pattern = re.escape(search.strip())
        mask = np.zeros(len(df), dtype=bool)
        for col in ["titre", "source", "pays", "region", "resume"]:
            mask |= (
                df[col].fillna("").str.contains(pattern, case=False, regex=True)
            ).to_numpy()
        df = df[mask]

    if sel_regions:
        df = df[df["region"].isin(sel_regions)]
    if sel_sectors:
        df = df[df["secteur"].isin(sel_sectors)]
    if sel_imp:
        df = df[df["importance"].isin(sel_imp)]

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start = pd.Timestamp(date_range[0])
        end = pd.Timestamp(date_range[1]) + timedelta(days=1)
        df = df[(df["_date"] >= start) & (df["_date"] < end)]

    df = df.drop(columns=["_date"])

    st.caption(f"{len(df)} information(s) affichée(s) sur {len(items)}.")

    display = df.rename(
        columns={
            "id": "ID",
            "date_ajout": "Date d'ajout",
            "titre": "Titre",
            "source": "Source",
            "lien": "Lien",
            "pays": "Pays",
            "region": "Région",
            "secteur": "Secteur",
            "resume": "Résumé",
            "importance": "Importance",
            "origine": "Origine",
        }
    )

    show_df(
        display,
        column_config={
            "Lien": st.column_config.LinkColumn(
                "Lien", display_text="Ouvrir"
            )
        },
    )

    st.download_button(
        "📥 Télécharger le flux filtré (CSV)",
        data=display.to_csv(index=False).encode("utf-8-sig"),
        file_name="stratos_intelligence_feed.csv",
        mime="text/csv",
    )

    # ---- Suppression ----
    with st.expander("🗑️ Supprimer des informations"):
        labels = {
            int(r["id"]): f"#{int(r['id'])} — {r['titre'][:80]}"
            for _, r in df.iterrows()
        }
        to_delete = st.multiselect(
            "Informations à supprimer",
            options=list(labels.keys()),
            format_func=lambda i: labels[i],
            key="feed_delete_select",
        )
        confirm = st.checkbox(
            "Je confirme la suppression définitive", key="feed_delete_confirm"
        )
        if st.button("Supprimer", key="feed_delete_btn"):
            if not to_delete:
                st.warning("Sélectionnez au moins une information.")
            elif not confirm:
                st.warning("Cochez la case de confirmation.")
            else:
                run_exec_many(
                    "DELETE FROM intelligence_items WHERE id = ?",
                    [(i,) for i in to_delete],
                )
                st.success(f"{len(to_delete)} information(s) supprimée(s).")
                st.rerun()


def page_intelligence_feed():
    st.header("📰 Intelligence Feed")
    st.write(
        "Collecte, structuration et suivi des informations "
        "économiques et stratégiques."
    )

    tab_list, tab_add, tab_rss = st.tabs(
        ["📚 Consulter", "➕ Ajouter", "📡 Import RSS"]
    )
    with tab_list:
        feed_list()
    with tab_add:
        feed_add_form()
    with tab_rss:
        feed_rss_import()


# ==================================================
# 6. COUNTRY RISK MONITOR
# ==================================================

def format_indicator_value(value, indicator_name):
    if "Population" in indicator_name or "PIB par habitant" in indicator_name:
        return f"{value:,.2f}"
    return f"{value:.2f} %"


def page_country_risk():
    st.header("🌍 Country Risk Monitor")
    st.write(
        "Indicateurs macroéconomiques issus de la Banque mondiale "
        "(données externes), utiles à l'analyse de l'environnement "
        "des affaires."
    )

    c1, c2 = st.columns(2)
    country_names = c1.multiselect(
        "Pays (1 à 5)",
        list(COUNTRIES.keys()),
        default=["Maroc"],
        max_selections=5,
    )
    indicator_name = c2.selectbox("Indicateur", list(WB_INDICATORS.keys()))

    current_year = datetime.now().year
    start_year, end_year = st.slider(
        "Période d'analyse",
        min_value=2000,
        max_value=current_year,
        value=(2010, current_year),
    )

    if not st.button("Analyser", type="primary", key="analyze_country"):
        return

    if not country_names:
        st.warning("Sélectionnez au moins un pays.")
        return

    indicator_code = WB_INDICATORS[indicator_name]
    frames = []

    try:
        with st.spinner("Récupération des données de la Banque mondiale..."):
            for name in country_names:
                df = fetch_wb_series(
                    COUNTRIES[name], indicator_code, start_year, end_year
                )
                if not df.empty:
                    df = df.copy()
                    df["Pays"] = name
                    frames.append(df)
    except requests.RequestException as error:
        st.error(f"Erreur de connexion à la Banque mondiale : {error}")
        return

    if not frames:
        st.warning(
            "Aucune donnée disponible pour cette sélection. "
            "Essayez un autre indicateur ou une autre période."
        )
        return

    data = pd.concat(frames, ignore_index=True)

    st.divider()
    st.subheader("Dernières observations")

    cols = st.columns(len(frames))
    for col, df in zip(cols, frames):
        latest = df.iloc[-1]
        country = df.iloc[-1]["Pays"]
        delta = None
        if len(df) >= 2:
            delta = f"{latest['Valeur'] - df.iloc[-2]['Valeur']:+.2f}"
        col.metric(
            f"{country} ({int(latest['Année'])})",
            format_indicator_value(latest["Valeur"], indicator_name),
            delta=delta,
            help="Variation par rapport à l'observation précédente "
            "disponible (pas nécessairement l'année précédente).",
        )

    st.subheader("Évolution historique")
    fig = px.line(
        data,
        x="Année",
        y="Valeur",
        color="Pays",
        markers=True,
        title=indicator_name,
        labels={"Valeur": indicator_name},
    )
    fig.update_layout(hovermode="x unified")
    show_chart(fig)

    with st.expander("Données détaillées"):
        show_df(data.sort_values(["Pays", "Année"], ascending=[True, False]))

    st.download_button(
        "📥 Télécharger les données (CSV)",
        data=data.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"STRATOS_{indicator_code}.csv",
        mime="text/csv",
    )
    st.caption(
        "Source : Banque mondiale, World Development Indicators. Les "
        "données peuvent être révisées et les années récentes peuvent "
        "manquer."
    )


# ==================================================
# 7. GLOBAL INTELLIGENCE MAP
# ==================================================

def page_world_map():
    st.header("🗺️ Global Intelligence Map")
    st.write(
        "Indicateurs économiques mondiaux (données externes de la "
        "Banque mondiale)."
    )

    years = list(range(datetime.now().year - 1, 2009, -1))

    c1, c2 = st.columns(2)
    indicator_name = c1.selectbox(
        "Indicateur à afficher", list(MAP_INDICATORS.keys())
    )
    year = c2.selectbox("Année", years, index=1)

    try:
        with st.spinner("Chargement des données mondiales..."):
            map_df = fetch_wb_world(MAP_INDICATORS[indicator_name], year)
    except requests.RequestException as error:
        st.error(f"Erreur de connexion à la Banque mondiale : {error}")
        return

    if map_df.empty:
        st.warning(
            "Aucune donnée pour cet indicateur et cette année. "
            "Essayez une année antérieure."
        )
        return

    fig = px.choropleth(
        map_df,
        locations="Code",
        locationmode="ISO-3",
        color="Valeur",
        hover_name="Pays",
        hover_data={"Code": True, "Valeur": ":,.2f"},
        color_continuous_scale=CYBER_SCALE,
        title=f"{indicator_name} — {year}",
    )
    style_geo(fig, height=560)
    show_chart(fig)

    st.metric("Observations disponibles", len(map_df))

    with st.expander("Consulter les données"):
        show_df(map_df.sort_values("Valeur", ascending=False))

    st.caption(
        "Source : Banque mondiale. Les pays sans donnée pour l'année "
        "choisie ne sont pas colorés."
    )


# ==================================================
# 8. FINANCIAL INTELLIGENCE
# ==================================================

FIN_COLUMNS = [
    "Entreprise",
    "Période",
    "Chiffre d'affaires",
    "EBIT",
    "Résultat net",
    "Total actifs",
    "Capitaux propres",
    "Dette financière",
    "Taux d'imposition (%)",
]


def safe_ratio(numerator, denominator, factor=100.0):
    """Division protégée : retourne NaN si le dénominateur est nul."""
    denom = denominator.replace(0, np.nan)
    return numerator / denom * factor


def compute_financials(raw):
    df = raw.copy()
    df = df[df["Entreprise"].fillna("").astype(str).str.strip() != ""]
    df["Période"] = df["Période"].fillna("").astype(str).str.strip()

    num_cols = [c for c in FIN_COLUMNS if c not in ("Entreprise", "Période")]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    ca = df["Chiffre d'affaires"]
    df["Marge opérationnelle (%)"] = safe_ratio(df["EBIT"], ca)
    df["Marge nette (%)"] = safe_ratio(df["Résultat net"], ca)
    df["ROA (%)"] = safe_ratio(df["Résultat net"], df["Total actifs"])
    df["ROE (%)"] = safe_ratio(df["Résultat net"], df["Capitaux propres"])
    df["NOPAT"] = df["EBIT"] * (1 - df["Taux d'imposition (%)"] / 100)
    capital_investi = df["Capitaux propres"] + df["Dette financière"]
    df["ROIC (%)"] = safe_ratio(df["NOPAT"], capital_investi)
    df["Dette / Capitaux propres"] = safe_ratio(
        df["Dette financière"], df["Capitaux propres"], factor=1.0
    )

    df = df.sort_values(["Entreprise", "Période"]).reset_index(drop=True)
    df["Croissance du CA (%)"] = (
        df.groupby("Entreprise")["Chiffre d'affaires"].pct_change() * 100
    )
    return df


def default_fin_data():
    """Trois entreprises FICTIVES sur trois exercices (exemple)."""
    rows = [
        ["Alpha SA (exemple)", "2022", 450000, 54000, 32000, 380000, 190000, 95000, 25.0],
        ["Alpha SA (exemple)", "2023", 520000, 67600, 41000, 410000, 215000, 100000, 25.0],
        ["Alpha SA (exemple)", "2024", 610000, 85400, 55000, 450000, 245000, 105000, 25.0],
        ["Beta Industries (exemple)", "2022", 300000, 21000, 9000, 310000, 120000, 130000, 30.0],
        ["Beta Industries (exemple)", "2023", 320000, 25600, 11500, 320000, 130000, 125000, 30.0],
        ["Beta Industries (exemple)", "2024", 335000, 30150, 14000, 330000, 140000, 120000, 30.0],
        ["Gamma Energie (exemple)", "2022", 800000, 96000, 60000, 700000, 350000, 180000, 28.0],
        ["Gamma Energie (exemple)", "2023", 780000, 78000, 48000, 720000, 355000, 200000, 28.0],
        ["Gamma Energie (exemple)", "2024", 830000, 99600, 63000, 740000, 370000, 190000, 28.0],
    ]
    return pd.DataFrame(rows, columns=FIN_COLUMNS)


def fin_summary_cards(result):
    """Lecture automatique sur la dernière période de chaque entreprise."""
    latest = result.groupby("Entreprise").tail(1)

    def best(col):
        sub = latest.dropna(subset=[col])
        if sub.empty:
            return "n/d", "non calculable"
        row = sub.loc[sub[col].idxmax()]
        return f"{row[col]:.1f}", str(row["Entreprise"])

    nopat_sub = latest.dropna(subset=["NOPAT"])
    if nopat_sub.empty:
        nopat_val, nopat_name = "n/d", "non calculable"
    else:
        row = nopat_sub.loc[nopat_sub["NOPAT"].idxmax()]
        nopat_val, nopat_name = f"{row['NOPAT']:,.0f}", str(row["Entreprise"])

    m_val, m_name = best("Marge nette (%)")
    r_val, r_name = best("ROE (%)")
    g_val, g_name = best("Croissance du CA (%)")

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Meilleure marge nette", f"{m_val} %", m_name, "green"),
                unsafe_allow_html=True)
    c2.markdown(kpi_card("Meilleur ROE", f"{r_val} %", r_name, "cyan"),
                unsafe_allow_html=True)
    c3.markdown(kpi_card("Meilleure croissance", f"{g_val} %", g_name, "amber"),
                unsafe_allow_html=True)
    c4.markdown(kpi_card("NOPAT le plus élevé", nopat_val, nopat_name, "violet"),
                unsafe_allow_html=True)


FIN_DB_COLS = {
    "Entreprise": "entreprise",
    "Période": "periode",
    "Chiffre d'affaires": "ca",
    "EBIT": "ebit",
    "Résultat net": "resultat_net",
    "Total actifs": "total_actifs",
    "Capitaux propres": "capitaux_propres",
    "Dette financière": "dette",
    "Taux d'imposition (%)": "taux_impot",
}


def clean_number(series):
    """Convertit en nombres, y compris les formats Excel français."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    txt = series.astype(str)
    for sep in (" ", "\u00a0", "\u202f"):
        txt = txt.str.replace(sep, "", regex=False)
    txt = txt.str.replace(",", ".", regex=False)
    return pd.to_numeric(txt, errors="coerce")


def fin_clean_df(df):
    out = df.copy()
    for col in FIN_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
    out = out[FIN_COLUMNS]
    out = out[out["Entreprise"].fillna("").astype(str).str.strip() != ""]
    out["Entreprise"] = out["Entreprise"].astype(str).str.strip()
    out["Période"] = out["Période"].fillna("").astype(str).str.strip()
    for col in FIN_COLUMNS[2:]:
        out[col] = clean_number(out[col])
    return out.reset_index(drop=True)


def fin_load_saved():
    select = ", ".join(f'{v} AS "{k}"' for k, v in FIN_DB_COLS.items())
    df = run_query(
        f"SELECT {select} FROM financial_records ORDER BY entreprise, periode"
    )
    return df


def fin_save(df):
    clean = fin_clean_df(df)
    clean = clean[clean["Période"] != ""]
    if clean.empty:
        return 0
    rows = []
    for _, r in clean.iterrows():
        values = [None if pd.isna(r[c]) else float(r[c]) for c in FIN_COLUMNS[2:]]
        rows.append((r["Entreprise"], r["Période"], *values))
    run_exec_many(
        """
        INSERT INTO financial_records
        (entreprise, periode, ca, ebit, resultat_net, total_actifs,
         capitaux_propres, dette, taux_impot)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (entreprise, periode) DO UPDATE SET
            ca = excluded.ca, ebit = excluded.ebit,
            resultat_net = excluded.resultat_net,
            total_actifs = excluded.total_actifs,
            capitaux_propres = excluded.capitaux_propres,
            dette = excluded.dette, taux_impot = excluded.taux_impot
        """,
        rows,
    )
    return len(rows)


def fin_known_companies():
    reg = run_query("SELECT nom FROM competitors ORDER BY nom")["nom"].tolist()
    saved = run_query(
        "SELECT DISTINCT entreprise FROM financial_records ORDER BY entreprise"
    )["entreprise"].tolist()
    return sorted(set(reg) | set(saved))


def fin_add_selection(current, companies, periods, include_saved):
    """Ajoute entreprise x période : données enregistrées sinon lignes vides."""
    saved = fin_load_saved()
    base = current.dropna(how="all") if len(current) else current
    existing = set()
    if len(base):
        tmp = fin_clean_df(base)
        existing = set(zip(tmp["Entreprise"], tmp["Période"]))

    new_rows = []
    for comp in companies:
        comp_periods = list(periods)
        if include_saved and not saved.empty:
            saved_periods = saved.loc[saved["Entreprise"] == comp, "Période"]
            comp_periods += [p for p in saved_periods if p not in comp_periods]
        for per in comp_periods:
            if (comp, per) in existing:
                continue
            match = saved[(saved["Entreprise"] == comp) & (saved["Période"] == per)]
            if not match.empty:
                new_rows.append(match.iloc[0].to_dict())
            else:
                row = {"Entreprise": comp, "Période": per}
                row.update({c: np.nan for c in FIN_COLUMNS[2:]})
                row["Taux d'imposition (%)"] = 25.0
                new_rows.append(row)

    add = pd.DataFrame(new_rows, columns=FIN_COLUMNS)
    if base is None or len(base) == 0:
        return add, len(new_rows)
    return pd.concat([base, add], ignore_index=True), len(new_rows)


def fin_parse_table(raw_df):
    """Accepte des en-têtes avec casse/accents légèrement différents."""
    lookup = {c.lower().strip(): c for c in FIN_COLUMNS}
    renamed = raw_df.rename(
        columns={c: lookup.get(str(c).lower().strip(), c) for c in raw_df.columns}
    )
    missing = [c for c in ("Entreprise", "Période") if c not in renamed.columns]
    if missing:
        raise ValueError(
            "Colonnes obligatoires absentes : " + ", ".join(missing)
            + ". Utilisez le modèle CSV proposé."
        )
    return fin_clean_df(renamed)


def fin_template_csv():
    sample = pd.DataFrame(
        [["Nom de l'entreprise", "2024", "", "", "", "", "", "", 25.0]],
        columns=FIN_COLUMNS,
    )
    return sample.to_csv(index=False).encode("utf-8-sig")


def fin_merge(current, imported):
    base = current.dropna(how="all") if len(current) else current
    merged = pd.concat([base, imported], ignore_index=True)
    merged = merged.drop_duplicates(subset=["Entreprise", "Période"], keep="last")
    return merged.reset_index(drop=True)


def fin_set_table(df):
    st.session_state["fin_data"] = df
    st.session_state.pop("fin_editor", None)
    st.rerun()


def fin_selector_panel(edited):
    """Panneau de sélection / enregistrement / import (affiché au-dessus)."""
    st.markdown(section_title("Choisir les entreprises"), unsafe_allow_html=True)

    companies = fin_known_companies()
    c1, c2 = st.columns([3, 2])
    chosen = c1.multiselect(
        "Entreprises (registre Competitive Intelligence + données enregistrées)",
        companies,
        key="fin_pick",
        placeholder="Choisissez une ou plusieurs entreprises",
    )
    periods_txt = c2.text_input(
        "Périodes à ajouter (séparées par des virgules)",
        value="2022, 2023, 2024",
        key="fin_periods",
    )
    include_saved = st.checkbox(
        "Inclure aussi toutes les périodes déjà enregistrées pour ces entreprises",
        value=True,
        key="fin_include_saved",
    )

    b1, b2, b3, b4 = st.columns(4)

    if b1.button("➕ Ajouter au tableau", key="fin_add", type="primary"):
        periods = [p.strip() for p in periods_txt.split(",") if p.strip()]
        if not chosen:
            st.warning("Sélectionnez au moins une entreprise.")
        elif not periods and not include_saved:
            st.warning("Indiquez au moins une période.")
        else:
            table, n = fin_add_selection(edited, chosen, periods, include_saved)
            st.session_state["fin_flash"] = f"{n} ligne(s) ajoutée(s) au tableau."
            fin_set_table(table)

    if b2.button("💾 Enregistrer le tableau", key="fin_save"):
        lines = [c for c in edited["Entreprise"].fillna("").astype(str)
                 if "(exemple)" in c]
        n = fin_save(edited)
        note = (
            " Les lignes « exemple » ont aussi été enregistrées : "
            "supprimez-les du tableau si vous ne les voulez pas."
            if lines else ""
        )
        st.session_state["fin_flash"] = (
            f"{n} ligne(s) enregistrée(s) durablement.{note}"
        )
        st.rerun()

    if b3.button("📂 Charger tout l'enregistré", key="fin_loadall"):
        saved = fin_load_saved()
        if saved.empty:
            st.warning("Aucune donnée enregistrée pour le moment.")
        else:
            fin_set_table(saved)

    if b4.button("🧹 Vider le tableau", key="fin_clear"):
        fin_set_table(pd.DataFrame(columns=FIN_COLUMNS))

    if "fin_flash" in st.session_state:
        st.success(st.session_state.pop("fin_flash"))

    with st.expander("📤 Importer en une fois (Excel collé ou fichier CSV)"):
        st.caption(
            "Copiez des cellules depuis Excel (avec la ligne d'en-têtes) et "
            "collez-les ci-dessous, ou envoyez un fichier CSV. Colonnes : "
            + ", ".join(FIN_COLUMNS)
            + ". Seules « Entreprise » et « Période » sont obligatoires."
        )
        st.download_button(
            "📥 Télécharger le modèle CSV",
            data=fin_template_csv(),
            file_name="stratos_modele_financier.csv",
            mime="text/csv",
            key="fin_template_dl",
        )
        pasted = st.text_area("Coller depuis Excel", key="fin_paste", height=120)
        uploaded = st.file_uploader(
            "…ou envoyer un fichier CSV", type=["csv", "txt"], key="fin_upload"
        )
        if st.button("Importer dans le tableau", key="fin_import"):
            try:
                if uploaded is not None:
                    raw_bytes = uploaded.getvalue()
                    try:
                        text = raw_bytes.decode("utf-8-sig")
                    except UnicodeDecodeError:
                        text = raw_bytes.decode("latin-1")
                elif pasted.strip():
                    text = pasted
                else:
                    st.warning("Collez des données ou envoyez un fichier.")
                    return
                raw_df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
                imported = fin_parse_table(raw_df)
                if imported.empty:
                    st.warning("Aucune ligne exploitable dans les données.")
                else:
                    st.session_state["fin_flash"] = (
                        f"{len(imported)} ligne(s) importée(s)."
                    )
                    fin_set_table(fin_merge(edited, imported))
            except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
                st.error(f"Import impossible : {error}")


def fin_tab_comparison():
    st.write(
        "Choisissez les entreprises dans la liste : les lignes se créent "
        "toutes seules (une par entreprise et par période). Remplissez les "
        "chiffres une seule fois, puis cliquez sur « Enregistrer » : ils "
        "seront automatiquement rechargés la prochaine fois. La croissance "
        "est calculée entre périodes successives d'une même entreprise "
        "(libellés triés par ordre alphabétique : 2023, 2024, 2024-T1...)."
    )

    if "fin_data" not in st.session_state:
        st.session_state["fin_data"] = default_fin_data()

    top = st.container()

    st.markdown(section_title("Tableau de saisie"), unsafe_allow_html=True)
    edited = st.data_editor(
        st.session_state["fin_data"],
        num_rows="dynamic",
        key="fin_editor",
        column_config={
            "Entreprise": st.column_config.TextColumn(required=True),
            "Période": st.column_config.TextColumn(required=True),
        },
    )

    with top:
        fin_selector_panel(edited)
        if st.button("↺ Recharger les exemples fictifs", key="fin_reset"):
            fin_set_table(default_fin_data())

    st.caption(
        "⚠️ Les entreprises « (exemple) » sont fictives : elles servent à "
        "illustrer l'outil et ne représentent aucune société réelle."
    )

    if edited.dropna(how="all").empty:
        st.info("Le tableau est vide : choisissez des entreprises ci-dessus.")
        return

    result = compute_financials(fin_clean_df(edited))
    if result.empty:
        st.info("Renseignez au moins un nom d'entreprise.")
        return

    st.markdown(section_title("Lecture automatique (dernière période)"),
                unsafe_allow_html=True)
    fin_summary_cards(result)

    st.markdown(section_title("Résultats calculés"), unsafe_allow_html=True)
    show_df(
        result.round(2),
        column_config={
            c: st.column_config.NumberColumn(format="%.2f")
            for c in result.columns
            if c not in ("Entreprise", "Période")
        },
    )

    metrics = [
        "Marge opérationnelle (%)",
        "Marge nette (%)",
        "ROA (%)",
        "ROE (%)",
        "ROIC (%)",
        "Croissance du CA (%)",
        "NOPAT",
        "Dette / Capitaux propres",
    ]
    metric = st.selectbox("Indicateur à visualiser", metrics, key="fin_metric")

    plot_df = result.dropna(subset=[metric])
    if plot_df.empty:
        st.info(
            "Pas de valeur calculable pour cet indicateur : complétez les "
            "chiffres dans le tableau."
        )
    else:
        fig = px.bar(
            plot_df,
            x="Période",
            y=metric,
            color="Entreprise",
            barmode="group",
            title=metric,
        )
        show_chart(fig)

    st.download_button(
        "📥 Exporter les calculs (CSV)",
        data=result.round(4).to_csv(index=False).encode("utf-8-sig"),
        file_name="stratos_financial_analysis.csv",
        mime="text/csv",
    )
    st.caption(
        "Données calculées par STRATOS à partir de vos saisies : leur "
        "fiabilité dépend de celle des chiffres que vous fournissez."
    )


def fin_tab_nopat():
    st.write("NOPAT = EBIT × (1 − taux d'imposition)")
    c1, c2 = st.columns(2)
    ebit = c1.number_input("EBIT (résultat opérationnel)", value=100000.0)
    tax = c2.number_input(
        "Taux d'imposition (%)", min_value=0.0, max_value=100.0, value=25.0
    )
    nopat = ebit * (1 - tax / 100)
    st.metric("NOPAT", f"{nopat:,.2f}")


def fin_tab_growth():
    st.write("Croissance entre deux périodes, et taux de croissance annuel moyen.")
    c1, c2, c3 = st.columns(3)
    prev = c1.number_input(
        "CA période précédente", min_value=0.0, value=100000.0
    )
    curr = c2.number_input("CA période actuelle", min_value=0.0, value=120000.0)
    years = c3.number_input(
        "Nombre d'années entre les deux", min_value=1, value=1, step=1
    )

    if prev <= 0:
        st.warning("Le chiffre d'affaires précédent doit être supérieur à zéro.")
        return

    growth = (curr - prev) / prev * 100
    cagr = ((curr / prev) ** (1 / years) - 1) * 100 if curr > 0 else None

    m1, m2 = st.columns(2)
    m1.metric("Croissance totale", f"{growth:+.2f} %")
    m2.metric(
        "Taux de croissance annuel moyen",
        f"{cagr:+.2f} %" if cagr is not None else "Non calculable",
    )


def page_financial():
    st.header("💹 Financial Intelligence")
    st.write(
        "Outils de calcul financier. Les résultats sont des données "
        "calculées à partir de vos saisies."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "📊 Comparaison entreprises / périodes",
            "🧮 NOPAT",
            "📈 Croissance & TCAM",
        ]
    )
    with tab1:
        fin_tab_comparison()
    with tab2:
        fin_tab_nopat()
    with tab3:
        fin_tab_growth()


# ==================================================
# 9. COMPETITIVE INTELLIGENCE
# ==================================================

def comp_add_form():
    with st.form("competitor_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nom = st.text_input("Nom de l'entreprise *")
            secteur = st.text_input("Secteur d'activité")
            pays = st.text_input("Pays principal d'activité")
            site = st.text_input("Site internet (facultatif)")
        with c2:
            menace = st.selectbox("Niveau de menace concurrentielle", MENACES)
            notes = st.text_area("Notes complémentaires")

        forces = st.text_area("Forces et avantages concurrentiels")
        faiblesses = st.text_area("Faiblesses")
        risques = st.text_area("Risques ou vulnérabilités identifiés")

        submitted = st.form_submit_button("Ajouter l'entreprise")

    if submitted:
        if not nom.strip():
            st.warning("Veuillez saisir le nom de l'entreprise.")
        else:
            run_exec(
                """
                INSERT INTO competitors
                (date_ajout, nom, secteur, pays, site, forces,
                 faiblesses, risques, menace, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    nom.strip(),
                    secteur.strip(),
                    pays.strip(),
                    site.strip(),
                    forces.strip(),
                    faiblesses.strip(),
                    risques.strip(),
                    menace,
                    notes.strip(),
                ),
            )
            st.success("Entreprise enregistrée durablement.")


def comp_registry():
    df = run_query("SELECT * FROM competitors ORDER BY id DESC")

    if df.empty:
        st.info("Aucune entreprise enregistrée pour le moment.")
        return

    search = st.text_input(
        "🔎 Recherche (nom, secteur, pays, forces, risques...)",
        key="comp_search",
    )
    c1, c2, c3 = st.columns(3)
    sectors = sorted(s for s in df["secteur"].dropna().unique() if s)
    countries = sorted(p for p in df["pays"].dropna().unique() if p)
    sel_sectors = c1.multiselect("Secteur", sectors, key="comp_sectors")
    sel_countries = c2.multiselect("Pays", countries, key="comp_countries")
    sel_threat = c3.multiselect("Menace", MENACES, key="comp_threat")

    view = df.copy()
    if search.strip():
        pattern = re.escape(search.strip())
        mask = np.zeros(len(view), dtype=bool)
        for col in ["nom", "secteur", "pays", "forces", "faiblesses",
                    "risques", "notes"]:
            mask |= (
                view[col].fillna("").str.contains(pattern, case=False, regex=True)
            ).to_numpy()
        view = view[mask]
    if sel_sectors:
        view = view[view["secteur"].isin(sel_sectors)]
    if sel_countries:
        view = view[view["pays"].isin(sel_countries)]
    if sel_threat:
        view = view[view["menace"].isin(sel_threat)]

    st.caption(f"{len(view)} entreprise(s) affichée(s) sur {len(df)}.")

    display = view.rename(
        columns={
            "id": "ID",
            "date_ajout": "Date d'ajout",
            "nom": "Entreprise",
            "secteur": "Secteur",
            "pays": "Pays",
            "site": "Site",
            "forces": "Forces",
            "faiblesses": "Faiblesses",
            "risques": "Risques",
            "menace": "Menace",
            "notes": "Notes",
        }
    )
    show_df(display)

    st.download_button(
        "📥 Exporter le registre (CSV)",
        data=display.to_csv(index=False).encode("utf-8-sig"),
        file_name="stratos_competitive_intelligence.csv",
        mime="text/csv",
    )

    with st.expander("🗑️ Supprimer des entreprises"):
        labels = {
            int(r["id"]): f"#{int(r['id'])} — {r['nom']}"
            for _, r in view.iterrows()
        }
        to_delete = st.multiselect(
            "Entreprises à supprimer",
            options=list(labels.keys()),
            format_func=lambda i: labels[i],
            key="comp_delete_select",
        )
        confirm = st.checkbox(
            "Je confirme la suppression définitive", key="comp_delete_confirm"
        )
        if st.button("Supprimer", key="comp_delete_btn"):
            if not to_delete:
                st.warning("Sélectionnez au moins une entreprise.")
            elif not confirm:
                st.warning("Cochez la case de confirmation.")
            else:
                run_exec_many(
                    "DELETE FROM competitors WHERE id = ?",
                    [(i,) for i in to_delete],
                )
                st.success(f"{len(to_delete)} entreprise(s) supprimée(s).")
                st.rerun()


def comp_compare():
    df = run_query("SELECT * FROM competitors ORDER BY nom")
    if len(df) < 2:
        st.info("Enregistrez au moins deux entreprises pour les comparer.")
        return

    labels = {int(r["id"]): f"{r['nom']} ({r['pays'] or 'pays n/a'})"
              for _, r in df.iterrows()}
    chosen = st.multiselect(
        "Entreprises à comparer (2 à 4)",
        options=list(labels.keys()),
        format_func=lambda i: labels[i],
        max_selections=4,
        key="comp_compare_select",
    )
    if len(chosen) < 2:
        st.info("Sélectionnez au moins deux entreprises.")
        return

    sub = df[df["id"].isin(chosen)].set_index("nom")
    table = sub[
        ["secteur", "pays", "site", "menace", "forces", "faiblesses",
         "risques", "notes"]
    ].rename(
        columns={
            "secteur": "Secteur",
            "pays": "Pays",
            "site": "Site",
            "menace": "Menace",
            "forces": "Forces",
            "faiblesses": "Faiblesses",
            "risques": "Risques",
            "notes": "Notes",
        }
    ).T
    table.index.name = "Critère"
    st.dataframe(table)

    st.download_button(
        "📥 Exporter la comparaison (CSV)",
        data=table.to_csv().encode("utf-8-sig"),
        file_name="stratos_comparaison_concurrents.csv",
        mime="text/csv",
    )


EXAMPLE_NOTE = "EXEMPLE — fiche indicative à vérifier et compléter"

EXAMPLE_COMPETITORS = [
    ("MTN Group", "Télécommunications", "Afrique du Sud (multi-pays)",
     "https://www.mtn.com",
     "Présence panafricaine, large base d'abonnés, services de paiement mobile.",
     "Revenus en monnaies locales, forte intensité capitalistique.",
     "Volatilité des changes, régulation locale, rapatriement des fonds.",
     "Élevée"),
    ("Orange Afrique & Moyen-Orient", "Télécommunications", "France / Afrique",
     "https://www.orange.com",
     "Réseau étendu en Afrique francophone, Orange Money, appui d'un grand groupe.",
     "Pression concurrentielle sur les prix des données et de la voix.",
     "Licences et taxes sectorielles, instabilité politique locale.",
     "Élevée"),
    ("Safaricom", "Télécommunications", "Kenya",
     "https://www.safaricom.co.ke",
     "Écosystème M-Pesa, position forte sur son marché, marque locale puissante.",
     "Concentration géographique.",
     "Régulation, risques d'exécution de l'expansion régionale.",
     "Moyenne"),
    ("Dangote Cement", "Industrie", "Nigeria",
     "https://www.dangotecement.com",
     "Grande capacité de production, intégration locale de la chaîne.",
     "Forte exposition au marché nigérian.",
     "Coûts de l'énergie, dévaluation de la monnaie, politique commerciale.",
     "Moyenne"),
    ("ACWA Power", "Énergie et infrastructures", "Arabie saoudite",
     "https://www.acwapower.com",
     "Spécialiste des projets d'énergie renouvelable et de dessalement.",
     "Projets très gourmands en capitaux, dépendance aux contrats d'achat d'électricité.",
     "Risque de contrepartie, délais de mise en œuvre.",
     "Élevée"),
    ("OCP Group", "Mines et ressources naturelles", "Maroc",
     "https://www.ocpgroup.ma",
     "Position de premier plan sur les phosphates et les engrais.",
     "Exposition aux cycles de prix des matières premières.",
     "Volatilité des prix des engrais, pression environnementale.",
     "Moyenne"),
]


def seed_competitors_if_needed():
    """Charge les fiches exemples une seule fois, si le registre est vide."""
    flag = run_query(
        "SELECT value FROM app_flags WHERE key = 'competitors_seeded'"
    )
    if not flag.empty:
        return
    count = int(run_query("SELECT COUNT(*) AS n FROM competitors")["n"].iloc[0])
    if count == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        rows = [
            (now, nom, sect, pays, site, forces, faiblesses, risques,
             menace, EXAMPLE_NOTE)
            for (nom, sect, pays, site, forces, faiblesses, risques,
                 menace) in EXAMPLE_COMPETITORS
        ]
        run_exec_many(
            """
            INSERT INTO competitors
            (date_ajout, nom, secteur, pays, site, forces,
             faiblesses, risques, menace, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    run_exec(
        "INSERT OR REPLACE INTO app_flags (key, value) "
        "VALUES ('competitors_seeded', '1')"
    )


def comp_example_cleanup():
    n = int(
        run_query(
            "SELECT COUNT(*) AS n FROM competitors WHERE notes LIKE 'EXEMPLE%'"
        )["n"].iloc[0]
    )
    if not n:
        return
    st.caption(
        f"{n} fiche(s) « EXEMPLE » présente(s) : descriptions générales à "
        "vérifier avant tout usage professionnel."
    )
    if st.button("🗑️ Supprimer les fiches exemples", key="comp_del_examples"):
        run_exec("DELETE FROM competitors WHERE notes LIKE 'EXEMPLE%'")
        st.rerun()


def page_competitive():
    seed_competitors_if_needed()

    st.header("🏢 Competitive Intelligence")
    st.write(
        "Registre permanent des entreprises, concurrents et partenaires "
        "surveillés."
    )

    tab1, tab2, tab3 = st.tabs(["📚 Registre", "➕ Ajouter", "⚖️ Comparer"])
    with tab1:
        comp_registry()
        comp_example_cleanup()
    with tab2:
        comp_add_form()
    with tab3:
        comp_compare()


# ==================================================
# 10. STRATEGIC DECISION LAB
# ==================================================

CRITERIA = {
    "Attractivité": False,
    "Faisabilité": False,
    "Risque": True,        # True = critère inversé (plus élevé = pire)
    "Coût d'entrée": True,
}


def weighted_scores(df, weights):
    total_weight = sum(weights.values())
    scores = pd.Series(0.0, index=df.index)
    for crit, inverted in CRITERIA.items():
        values = 11 - df[crit] if inverted else df[crit]
        scores += values * weights[crit]
    return (scores / total_weight).round(2)


def build_report(decision, df, weights, equal_df):
    lines = []
    lines.append("# Rapport de décision stratégique — STRATOS")
    lines.append("")
    lines.append(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Préparé par : {OWNER_NAME}, {OWNER_TITLE} — {ORG_NAME}")
    lines.append(f"Décision étudiée : {decision or 'Non renseignée'}")
    lines.append("")
    lines.append("## Pondération des critères")
    for crit, w in weights.items():
        note = " (critère inversé : une valeur élevée pénalise)" \
            if CRITERIA[crit] else ""
        lines.append(f"- {crit} : {w}{note}")
    lines.append("")
    lines.append("## Classement")
    for rank, (_, row) in enumerate(df.iterrows(), start=1):
        cout = row["Coût d'entrée"]
        lines.append(
            f"{rank}. **{row['Scénario']}** — score {row['Score pondéré']}/10 "
            f"(attractivité {row['Attractivité']}, faisabilité "
            f"{row['Faisabilité']}, risque {row['Risque']}, "
            f"coût d'entrée {cout})"
        )
    lines.append("")

    best = df.iloc[0]
    lines.append("## Synthèse")
    if len(df) > 1:
        gap = round(best["Score pondéré"] - df.iloc[1]["Score pondéré"], 2)
        lines.append(
            f"Le scénario **{best['Scénario']}** obtient le meilleur score "
            f"({best['Score pondéré']}/10), avec un écart de {gap} point(s) "
            f"sur **{df.iloc[1]['Scénario']}**."
        )
        if gap < 0.5:
            lines.append(
                "L'écart est faible : le classement est fragile et dépend "
                "fortement des hypothèses de notation."
            )
    equal_best = equal_df.iloc[0]["Scénario"]
    if equal_best != best["Scénario"]:
        lines.append(
            f"Attention : avec des poids égaux, le premier serait "
            f"**{equal_best}**. Le résultat est sensible à la pondération."
        )
    else:
        lines.append(
            "Le classement de tête est identique avec des poids égaux : "
            "il est robuste à la pondération."
        )
    lines.append("")
    lines.append(
        "_Ce score est un outil d'aide à la réflexion fondé sur des notes "
        "subjectives. Il ne remplace pas une analyse détaillée des coûts, "
        "des risques et des hypothèses de chaque scénario._"
    )
    return "\n".join(lines)


DEFAULT_DECISION = "Choisir le pays d'implantation d'un bureau régional en Afrique"
DEFAULT_WEIGHTS = {
    "Attractivité": 8,
    "Faisabilité": 6,
    "Risque": 7,
    "Coût d'entrée": 4,
}


def default_scenarios():
    return pd.DataFrame(
        {
            "Scénario": [
                "Maroc (Casablanca)",
                "Côte d'Ivoire (Abidjan)",
                "Kenya (Nairobi)",
                "Sénégal (Dakar)",
            ],
            "Attractivité": [8, 8, 7, 6],
            "Faisabilité": [8, 7, 7, 7],
            "Risque": [3, 4, 4, 4],
            "Coût d'entrée": [6, 5, 5, 4],
        }
    )


def page_decision_lab():
    st.header("🧭 Strategic Decision Lab")
    st.write(
        "Comparez des scénarios d'investissement ou d'implantation avec "
        "des critères pondérés. Les résultats se mettent à jour "
        "automatiquement à chaque modification."
    )
    st.caption(
        "⚠️ Le cas ci-dessous est un exemple avec des notes illustratives "
        "(non issues d'une étude). Ajustez-les selon votre propre analyse, "
        "par exemple à l'aide du Country Risk Monitor et de la Fiche pays."
    )

    if st.button("↺ Recharger l'exemple", key="lab_reset"):
        for key in list(st.session_state.keys()):
            if key.startswith("weight_") or key in (
                "scenarios", "scenario_editor", "lab_decision"
            ):
                del st.session_state[key]
        st.rerun()

    decision = st.text_input(
        "Décision à prendre", value=DEFAULT_DECISION, key="lab_decision"
    )

    st.markdown(section_title("1. Pondération des critères"),
                unsafe_allow_html=True)
    st.caption("0 = ignoré, 10 = très important.")
    cols = st.columns(len(CRITERIA))
    weights = {}
    for col, crit in zip(cols, CRITERIA):
        suffix = " (inversé)" if CRITERIA[crit] else ""
        weights[crit] = col.slider(
            crit + suffix, 0, 10, DEFAULT_WEIGHTS[crit], key=f"weight_{crit}"
        )

    st.markdown(section_title("2. Notation des scénarios"),
                unsafe_allow_html=True)
    st.caption(
        "Notes de 1 à 10. Pour « Risque » et « Coût d'entrée », "
        "10 = très risqué / très coûteux (ces critères pénalisent le score)."
    )

    if "scenarios" not in st.session_state:
        st.session_state["scenarios"] = default_scenarios()

    num_cfg = {
        crit: st.column_config.NumberColumn(
            crit, min_value=1, max_value=10, step=1, default=5
        )
        for crit in CRITERIA
    }
    edited = st.data_editor(
        st.session_state["scenarios"],
        num_rows="dynamic",
        key="scenario_editor",
        column_config=num_cfg,
    )

    df = edited.copy()
    df = df[df["Scénario"].fillna("").astype(str).str.strip() != ""]
    for crit in CRITERIA:
        df[crit] = pd.to_numeric(df[crit], errors="coerce")
    df = df.dropna(subset=list(CRITERIA)).reset_index(drop=True)

    if len(df) < 2:
        st.warning("Saisissez au moins deux scénarios complets.")
        return
    if sum(weights.values()) == 0:
        st.warning("Au moins un critère doit avoir un poids supérieur à zéro.")
        return

    df["Score pondéré"] = weighted_scores(df, weights)
    ranked = df.sort_values("Score pondéré", ascending=False).reset_index(
        drop=True
    )
    ranked.insert(0, "Rang", range(1, len(ranked) + 1))

    equal_df = df.copy()
    equal_df["Score pondéré"] = weighted_scores(
        equal_df, {c: 1 for c in CRITERIA}
    )
    equal_df = equal_df.sort_values(
        "Score pondéré", ascending=False
    ).reset_index(drop=True)

    st.markdown(section_title("3. Résultats"), unsafe_allow_html=True)

    best = ranked.iloc[0]
    k1, k2, k3 = st.columns(3)
    k1.markdown(kpi_card("Scénario en tête", best["Scénario"],
                         "selon votre pondération", "green"),
                unsafe_allow_html=True)
    k2.markdown(kpi_card("Score", f"{best['Score pondéré']}/10", "", "cyan"),
                unsafe_allow_html=True)
    gap = round(best["Score pondéré"] - ranked.iloc[1]["Score pondéré"], 2)
    k3.markdown(kpi_card("Écart avec le 2e", f"{gap} pt",
                         "faible = classement fragile" if gap < 0.5 else "net",
                         "amber" if gap < 0.5 else "violet"),
                unsafe_allow_html=True)

    st.write("")
    show_df(ranked)

    if equal_df.iloc[0]["Scénario"] != best["Scénario"]:
        st.warning(
            "Sensibilité : avec des poids égaux, le premier serait "
            f"{equal_df.iloc[0]['Scénario']}. Le résultat dépend de votre "
            "pondération."
        )

    left, right = st.columns(2)
    with left:
        fig_bar = px.bar(
            ranked, x="Scénario", y="Score pondéré", range_y=[0, 10],
            title="Scores pondérés", text="Score pondéré",
        )
        show_chart(fig_bar)

    with right:
        radar_rows = []
        for _, row in df.iterrows():
            for crit, inverted in CRITERIA.items():
                value = 11 - row[crit] if inverted else row[crit]
                label = f"{crit} (inversé)" if inverted else crit
                radar_rows.append(
                    {"Scénario": row["Scénario"], "Critère": label,
                     "Note": value}
                )
        fig_radar = px.line_polar(
            pd.DataFrame(radar_rows), r="Note", theta="Critère",
            color="Scénario", line_close=True, range_r=[0, 10],
            title="Profil des scénarios (plus haut = mieux)",
        )
        show_chart(fig_radar)

    report = build_report(decision, ranked, weights, equal_df)
    st.markdown(section_title("4. Rapport synthétique"),
                unsafe_allow_html=True)
    st.markdown(report)

    c1, c2 = st.columns(2)
    c1.download_button(
        "📥 Télécharger le rapport (Markdown)",
        data=report.encode("utf-8"),
        file_name="stratos_rapport_decision.md",
        mime="text/markdown",
    )
    c2.download_button(
        "📥 Télécharger le classement (CSV)",
        data=ranked.to_csv(index=False).encode("utf-8-sig"),
        file_name="stratos_classement_scenarios.csv",
        mime="text/csv",
    )


# ==================================================
# 11. NAVIGATION ET LANCEMENT
# ==================================================

MODULES = {
    "Dashboard": page_dashboard,
    "Live Monitor": page_live_monitor,
    "Intelligence Feed": page_intelligence_feed,
    "Country Risk Monitor": page_country_risk,
    "Global Intelligence Map": page_world_map,
    "Financial Intelligence": page_financial,
    "Competitive Intelligence": page_competitive,
    "Strategic Decision Lab": page_decision_lab,
}


def main():
    now_utc = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    st.markdown(
        '<div class="topbar"><div class="brand">STRATOS'
        '<span>// STRATEGIC INTELLIGENCE PLATFORM</span></div>'
        f'<div class="status"><span class="dot"></span>SYSTÈME EN LIGNE · {now_utc}'
        f' &nbsp;·&nbsp; <span style="font-size:.6rem;opacity:.7">'
        f'{esc(OWNER_NAME)} — {esc(ORG_NAME)}</span></div></div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            '<div class="brand" style="font-size:1.1rem;margin-bottom:6px;">'
            '🌐 STRATOS</div>',
            unsafe_allow_html=True,
        )
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=120)
        st.markdown(
            f'<div style="font-size:.6rem;color:#64748B;letter-spacing:.06em;'
            f'margin:-4px 0 10px;">{esc(OWNER_NAME)} · {esc(ORG_NAME)}</div>',
            unsafe_allow_html=True,
        )
        module = st.radio("Navigation", list(MODULES.keys()))
        st.divider()
        st.caption(
            "🟢 Données en direct : Google Actualités, USGS, "
            "open.er-api.com.\n\n"
            "🔵 Données externes : Banque mondiale.\n\n"
            "🟣 Données saisies : vos informations.\n\n"
            "⚙️ Données calculées : résultats STRATOS."
        )
        st.caption("STRATOS | Version 2.0")

    MODULES[module]()


main()