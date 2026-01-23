import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
import random

st.set_page_config(page_title="Dynamischer Sparplan-Rechner", layout="wide")

# -----------------------------
# Helpers: Session State
# -----------------------------
if "result" not in st.session_state:
    st.session_state.result = None
if "last_info_limits" not in st.session_state:
    st.session_state.last_info_limits = []
if "last_info_adjustments" not in st.session_state:
    st.session_state.last_info_adjustments = []

# -----------------------------
# Logo und Branding
# -----------------------------
from PIL import Image  # noqa
import base64

file_path = "Traderise_Logo.PNG"
with open(file_path, "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode()

branding_html = f"""
<div style="display: flex; align-items: center; margin-top: 10px; margin-bottom: 30px;">
    <img src="data:image/png;base64,{encoded_image}" alt="Logo" style="width: 50px; height: auto; margin-right: 10px;">
    <span style="font-size: 14px;">Powered by <a href="https://traderise.net" target="_blank" style="color:#1E90FF; text-decoration: none;">Traderise.net</a></span>
</div>
"""
st.markdown(branding_html, unsafe_allow_html=True)

st.title("Dynamischer Sparplan-Rechner")

# -----------------------------
# Defaults
# -----------------------------
default_favoriten = """ASML
TSMC
Micron
Palantir
Vertiv
Siemens Energy
Coinbase
Alphabet
NVIDIA
Crowdstrike"""

default_aktien = """Adyen
Aker Carbon Capture
Airbnb (A)
Alibaba Group (ADR)
AMD
Amazon.com
Apple
AST SpaceMobile
Axon Enterprise
Berkshire Hathaway (B)
BitMine Immersion Technology
Block
BYD
BMW
Brookfield Asset Management
Cameco
Circle Internet Group
Cloudflare (A)
Critical Metals
Constellation Energy
Covestro
Cummins
Datadog (A)
Deutsche Telekom
Digindex
DroneShield
D-Wave Quantum
Eli Lilly & Co
Evonik Industries
Fortinet
Galaxy Digital Inc. Reg. Shs. Cl…
Heidelberg Materials
Hensoldt
Illumina
Impala Platinum
Infineon Technologies
Intellia Therapeutics
Intellistake Technologies
Intel
Intuitive Surgical
Johnson & Johnson
KLA
Lam Research
LVMH Louis Vuitton Moet Hen…
MercadoLibre
Mercedes-Benz Group
Meta Platforms (A)
MicroStrategy (A)
Microsoft
MP Materials
Netflix
Nio
Nordex
Novo Nordisk (ADR)
Ondas Holdings
Oracle
Palo Alto Networks
Procter & Gamble
Quantum eMotion
Realty Income
RENK Group
Rheinmetall
Rocket Lab Corp.
Saab (B)
SAP
Schaeffler
ServiceNow
Shopify (A)
Siemens
SK Hynix (GDR)
Snowflake (A)
Spotify Technology
Take-Two Interactive
Tencent Holdings
Tesla
Thales
The Trade Desk (A)
ThyssenKrupp
TKMS AG & Co. KGaA Inhaber-…
Xiaomi
"""

default_etfs = """AI & Big Data USD (Acc)
Automation & Robotics USD (Acc)
BlackRock World Mining Trust
Core MSCI World USD (Acc)
Core Stoxx Europe 600 EUR (Acc)
Defence USD (Acc)
MSCI EM USD (Acc)
MSCI World Small Cap USD (Acc)
Physical Gold USD (Acc)
Space Innovators USD (Acc)
"""

# -----------------------------
# Helper
# -----------------------------
def clean_lines(text: str):
    lines = []
    for raw in text.splitlines():
        x = raw.strip().replace("“", '"').replace("”", '"').replace("’", "'")
        x = " ".join(x.split())
        if x:
            lines.append(x)
    return lines

def etf_weight_for(name: str) -> float:
    n = name.lower()
    if "core msci world" in n:
        return 0.25
    if "blackrock world mining" in n:
        return 0.05
    if "automation & robotics" in n:
        return 0.05
    if "msci world small cap" in n:
        return 0.05
    return 0.10

def pick_etfs(etf_list, max_count: int):
    if len(etf_list) <= max_count:
        return etf_list
    weights = {e: etf_weight_for(e) for e in etf_list}
    order_index = {e: i for i, e in enumerate(etf_list)}
    sorted_etfs = sorted(etf_list, key=lambda e: (-weights.get(e, 0.10), order_index.get(e, 10_000)))
    return sorted_etfs[:max_count]

def profile_seed(profile: str) -> int:
    mapping = {
        "Ausgewogen (Standard)": 420,
        "Tech & AI": 1337,
        "Wachstum": 2024,
        "Dividenden & Value": 777,
        "Konservativ & defensiv": 99
    }
    return mapping.get(profile, 420)

# -----------------------------
# Tagging: ALLE Rotation-Aktien bekommen Tags
# -----------------------------
ALL_TAGS = {
    "Semis": [
        "ASML","TSMC","Micron","AMD","Intel","Infineon Technologies","SK Hynix (GDR)","KLA","Lam Research"
    ],
    "Software/Cloud": [
        "Microsoft","Oracle","SAP","ServiceNow","Snowflake (A)","Cloudflare (A)","Datadog (A)","Meta Platforms (A)","Alphabet"
    ],
    "Cyber": [
        "Crowdstrike","Fortinet","Palo Alto Networks"
    ],
    "AI/Data": [
        "Palantir","The Trade Desk (A)"
    ],
    "FinTech/Crypto": [
        "Coinbase","MicroStrategy (A)","Block","Circle Internet Group","Digindex","BitMine Immersion Technology"
    ],
    "Quantum": [
        "D-Wave Quantum","Quantum eMotion"
    ],
    "Space": [
        "AST SpaceMobile","Ondas Holdings","Rocket Lab Corp."
    ],
    "Robotics/Drone": [
        "DroneShield","Axon Enterprise"
    ],

    "Platform/Consumer": [
        "Airbnb (A)","Netflix","Spotify Technology","Shopify (A)","MercadoLibre","Take-Two Interactive",
        "Alibaba Group (ADR)","Amazon.com","Apple","Tencent Holdings","Xiaomi"
    ],
    "EV/Auto": [
        "Tesla","BYD","Nio","BMW","Mercedes-Benz Group"
    ],

    "Holding/Quality": [
        "Berkshire Hathaway (B)","Brookfield Asset Management"
    ],
    "Staples": [
        "Procter & Gamble"
    ],
    "Telecom": [
        "Deutsche Telekom"
    ],
    "Healthcare/Pharma": [
        "Johnson & Johnson","Novo Nordisk (ADR)","Eli Lilly & Co","Intuitive Surgical","Illumina"
    ],
    "Biotech": [
        "Intellia Therapeutics","Intellistake Technologies"
    ],

    "Industrials": [
        "Siemens","Siemens Energy","Cummins","Schaeffler","ThyssenKrupp","TKMS AG & Co. KGaA Inhaber-…",
        "Nordex","Constellation Energy","RENK Group"
    ],
    "Materials/Chemicals": [
        "Heidelberg Materials","Covestro","Evonik Industries","Impala Platinum"
    ],
    "Mining/Metals": [
        "Cameco","Critical Metals","MP Materials"
    ],
    "Defense/Aerospace": [
        "Rheinmetall","Saab (B)","Thales","Hensoldt"
    ],

    "REIT": [
        "Realty Income"
    ],
    "Carbon/ESG": [
        "Aker Carbon Capture"
    ],
    "Luxury": [
        "LVMH Louis Vuitton Moet Hen…"
    ],
    "Other": [
        "Adyen"
    ],
}

RISK_TAGS = {
    "High Volatility": [
        "Coinbase","MicroStrategy (A)","BitMine Immersion Technology","Digindex","Nio"
    ],
    "Early/Speculative": [
        "Quantum eMotion","D-Wave Quantum","Ondas Holdings","DroneShield","AST SpaceMobile"
    ],
}

PROFILE_WANTED_TAGS = {
    "Ausgewogen (Standard)": [],
    "Tech & AI": ["Semis", "Software/Cloud", "Cyber", "AI/Data", "Quantum", "Robotics/Drone", "FinTech/Crypto"],
    "Wachstum": ["Platform/Consumer", "EV/Auto", "Biotech", "Space", "FinTech/Crypto", "AI/Data"],
    "Dividenden & Value": ["Holding/Quality", "Staples", "Telecom", "Healthcare/Pharma", "Industrials", "Materials/Chemicals", "Mining/Metals", "Luxury", "REIT"],
    "Konservativ & defensiv": ["Holding/Quality", "Staples", "Telecom", "Healthcare/Pharma", "Industrials", "REIT", "Materials/Chemicals"],
}

def normalize_name(x: str) -> str:
    x = x.strip().lower()
    x = x.replace("…", "...")  # normalize ellipsis if present
    x = re.sub(r"\(a\)|\(b\)", "", x)
    x = x.replace("adr", "")
    x = re.sub(r"[^a-z0-9\s\.\-&]", "", x)
    x = re.sub(r"\s+", " ", x).strip()
    return x

_TAG_LOOKUP = {}
for tag, names in ALL_TAGS.items():
    for n in names:
        _TAG_LOOKUP.setdefault(normalize_name(n), set()).add(tag)

_RISK_LOOKUP = {}
for tag, names in RISK_TAGS.items():
    for n in names:
        _RISK_LOOKUP.setdefault(normalize_name(n), set()).add(tag)

def tags_for_rotation(name: str) -> list[str]:
    n = normalize_name(name)
    tags = set()

    if n in _TAG_LOOKUP:
        tags |= _TAG_LOOKUP[n]
    else:
        for key_norm, tset in _TAG_LOOKUP.items():
            if key_norm and (key_norm in n or n in key_norm):
                tags |= tset

    risk = set()
    if n in _RISK_LOOKUP:
        risk |= _RISK_LOOKUP[n]
    else:
        for key_norm, tset in _RISK_LOOKUP.items():
            if key_norm and (key_norm in n or n in key_norm):
                risk |= tset

    tags |= risk

    if not tags:
        tags = {"Unkategorisiert"}

    return sorted(tags)

def score_rotation(name: str, profile: str) -> int:
    tags = tags_for_rotation(name)
    wanted = set(PROFILE_WANTED_TAGS.get(profile, []))

    if profile == "Ausgewogen (Standard)":
        if "High Volatility" in tags or "Early/Speculative" in tags:
            return -1
        return 0

    score = 0
    for t in tags:
        if t in wanted:
            score += 3

    if profile in ["Dividenden & Value", "Konservativ & defensiv"]:
        if "High Volatility" in tags:
            score -= 4
        if "Early/Speculative" in tags:
            score -= 3

    if profile == "Konservativ & defensiv":
        if "Semis" in tags or "Quantum" in tags or "FinTech/Crypto" in tags:
            score -= 1

    return score

def explain_rotation(name: str, profile: str) -> list[str]:
    tags = tags_for_rotation(name)
    wanted = set(PROFILE_WANTED_TAGS.get(profile, []))
    hits = [t for t in tags if t in wanted]
    return hits[:3] if hits else tags[:2]

def pick_rotation_by_profile(
    rot_list: list[str],
    profile: str,
    strength: str,
    repeatable: bool,
    do_shuffle: bool,
    desired_pool_size: int | None = None
) -> list[str]:
    if not rot_list:
        return []

    seed = profile_seed(profile) if repeatable else None
    random.seed(seed)

    scored = []
    for s in rot_list:
        sc = score_rotation(s, profile)
        tie = random.random() if do_shuffle else 0.0
        scored.append((sc, tie, s))

    scored.sort(key=lambda t: (-t[0], t[1]))

    if profile == "Ausgewogen (Standard)":
        ordered = [t[2] for t in scored] if do_shuffle else rot_list[:]
        return ordered[:desired_pool_size] if desired_pool_size else ordered

    positives = [t for t in scored if t[0] > 0]
    rest = [t for t in scored if t[0] <= 0]

    if strength in ["Mild", "Normal"]:
        ordered = [t[2] for t in positives] + [t[2] for t in rest]
    else:  # Strong
        ordered_pos = [t[2] for t in positives]
        ordered_all = [t[2] for t in scored]
        if len(ordered_pos) >= max(5, int(0.3 * len(rot_list))):
            ordered = ordered_pos + [t[2] for t in rest]
        else:
            ordered = ordered_all

    if desired_pool_size:
        return ordered[:desired_pool_size]
    return ordered

def render_two_col_grid(items: list[str]):
    if not items:
        st.caption("—")
        return
    left, right = st.columns(2)
    half = (len(items) + 1) // 2
    left_items = items[:half]
    right_items = items[half:]
    with left:
        for it in left_items:
            st.markdown(f"- {it}")
    with right:
        for it in right_items:
            st.markdown(f"- {it}")

# -----------------------------
# UI: Inputs in a form
# -----------------------------
with st.form("inputs_form", clear_on_submit=False):
    st.subheader("Eingaben")

    zielsumme = st.number_input("Zielsumme (€)", value=50000, key="zielsumme")
    monate = st.number_input("Dauer (Monate)", value=100, key="monate")
    aktienanteil = st.slider("Aktienanteil (%)", 0, 100, 65, key="aktienanteil")
    etf_anteil = 100 - aktienanteil

    monatlicher_betrag_preview = zielsumme / monate if monate else 0
    st.markdown(f"**ETFs erhalten {etf_anteil} %, Aktien erhalten {aktienanteil} %**")
    st.markdown(f"### Monatlicher Sparbetrag: {monatlicher_betrag_preview:.2f} €")

    anzahl_aktien_pro_monat = st.number_input(
        "Wie viele Aktien pro Monat besparen?",
        min_value=3, max_value=15, value=7, key="anzahl_aktien_pro_monat"
    )
    st.caption("Favoriten werden pro Aktie stärker bespart als Rotation. Rotation-Aktien werden automatisch ergänzt.")

    favoriten = st.text_area("Favoritenaktien (eine pro Zeile)", value=default_favoriten, key="favoriten")
    st.caption("Falls keine Favoriten angegeben sind, wird das gesamte Aktienbudget auf rotierende Aktien verteilt.")

    rotation_aktien = st.text_area("Weitere Aktien (eine pro Zeile)", value=default_aktien, key="rotation_aktien")
    etfs = st.text_area("ETFs (eine pro Zeile)", value=default_etfs, key="etfs")
    st.caption("Falls keine ETFs angegeben sind, wird das gesamte Kapital auf Aktien verteilt.")

    st.subheader("⚙️ Erweiterte Einstellungen")

    # ✅ Checkbox entfernt -> Limits immer sichtbar
    max_aktien = st.number_input(
        "Max. Aktien im Plan (inkl. Favoriten)",
        min_value=5, max_value=200, value=40, step=1, key="max_aktien"
    )
    st.caption("Default: **40** (wie vorher im Einfach-Modus).")

    max_etfs = st.number_input(
        "Max. ETFs im Plan",
        min_value=1, max_value=50, value=10, step=1, key="max_etfs"
    )
    st.caption("Default: **10** (wie vorher im Einfach-Modus).")

    begrenze_rotation = st.checkbox(
        "Rotation-Liste automatisch kürzen (nur so viele, wie im Zeitraum bespart werden können)",
        value=True, key="begrenze_rotation"
    )

    profil = st.selectbox(
        "Anlage-Profil (steuert Rotation-Auswahl)",
        options=[
            "Ausgewogen (Standard)",
            "Tech & AI",
            "Wachstum",
            "Dividenden & Value",
            "Konservativ & defensiv",
        ],
        index=0, key="profil"
    )

    auswahl_wiederholbar = st.checkbox(
        "Auswahl wiederholbar (gleiches Profil + gleiche Inputs = gleiche Reihenfolge)",
        value=True, key="auswahl_wiederholbar"
    )

    shuffle_rotation = st.checkbox(
        "Rotation mischen (empfohlen – verhindert Alphabet-Reihenfolge)",
        value=True, key="shuffle_rotation"
    )

    with st.expander("🔧 Optional (Advanced)", expanded=False):
        profil_staerke = st.selectbox(
            "Profil-Stärke (wie stark das Profil die Rotation beeinflusst)",
            options=["Mild", "Normal", "Strong"],
            index=2, key="profil_staerke"
        )
        show_tag_table = st.checkbox("Rotation-Kategorisierung anzeigen (Tabelle)", value=False, key="show_tag_table")
        st.caption("Mild = wenig Filter • Strong = harter Filter (Fallback wenn zu wenige Treffer)")
    profil_staerke = st.session_state.get("profil_staerke", "Strong")
    show_tag_table = st.session_state.get("show_tag_table", False)

    favs_pro_monat = st.slider("Wie viele Favoriten pro Monat besparen?", 1, 3, 2, key="favs_pro_monat")

    auto_modus = st.checkbox(
        "Auto-Modus: Favoriten-Multiplikator fix (empfohlen für Anfänger)",
        value=True, key="auto_modus"
    )

    min_rate_rotation = st.number_input(
        "Mindestbetrag pro Rotation-Aktie (€/Monat) – falls nötig wird die Anzahl Rotation-Aktien pro Monat automatisch reduziert",
        min_value=0.0, value=20.0, step=1.0, key="min_rate_rotation"
    )

    FAV_MULTIPLIER_AUTO = 1.5
    if auto_modus:
        fav_multiplier = FAV_MULTIPLIER_AUTO
        st.caption(f"Auto-Modus aktiv: Favoriten werden pro Aktie mit **{fav_multiplier:.2f}x** gegenüber Rotation gewichtet.")
    else:
        fav_multiplier = st.slider(
            "Favoriten stärker besparen als Rotation (pro Aktie, Multiplikator)",
            min_value=1.0, max_value=3.0, value=1.5, step=0.1, key="fav_multiplier"
        )

    top_n_chart = st.slider("Diagramm: Anzahl angezeigter Positionen", 10, 120, 40, key="top_n_chart")
    submitted = st.form_submit_button("Sparplan berechnen")

# -----------------------------
# Compute (only when submitted) -> store in session_state
# -----------------------------
def compute_plan(
    zielsumme, monate, aktienanteil, anzahl_aktien_pro_monat,
    favoriten_text, rotation_text, etfs_text,
    max_aktien, max_etfs, begrenze_rotation,
    profil, profil_staerke, auswahl_wiederholbar, shuffle_rotation,
    favs_pro_monat, fav_multiplier, min_rate_rotation, top_n_chart, show_tag_table
):
    info_limits = []
    info_adjustments = []

    fav_list_raw = clean_lines(favoriten_text)
    rot_list_raw = clean_lines(rotation_text)
    etf_list_raw = clean_lines(etfs_text)

    if not monate or monate <= 0:
        raise ValueError("Die Dauer (Monate) muss größer als 0 sein.")

    etf_anteil_local = 100 - aktienanteil
    if not etf_list_raw:
        aktienanteil_local = 100
        etf_anteil_local = 0
    else:
        aktienanteil_local = aktienanteil

    monatlicher_betrag = zielsumme / monate
    aktien_budget = monatlicher_betrag * aktienanteil_local / 100
    etf_budget = monatlicher_betrag * etf_anteil_local / 100

    # ETFs limitieren
    etf_list = pick_etfs(etf_list_raw, int(max_etfs)) if etf_list_raw else []
    if len(etf_list_raw) > len(etf_list):
        info_limits.append(f"ETF-Limit aktiv: {len(etf_list_raw)} eingegeben → **{len(etf_list)}** werden verwendet.")

    # Aktien-Limit: Rotation wird PROFIL-BASIERT gepickt
    fav_list = fav_list_raw[:]
    rot_list_all = rot_list_raw[:]
    max_aktien_int = int(max_aktien)

    if len(fav_list) > max_aktien_int:
        fav_list = fav_list[:max_aktien_int]
        rot_list = []
        info_limits.append(f"Aktien-Limit: Favoriten > Max. Aktien → Favoriten auf {max_aktien_int} gekürzt, Rotation deaktiviert.")
    else:
        rot_slots = max_aktien_int - len(fav_list)
        rot_list_picked = pick_rotation_by_profile(
            rot_list_all,
            profile=profil,
            strength=profil_staerke,
            repeatable=auswahl_wiederholbar,
            do_shuffle=shuffle_rotation,
            desired_pool_size=rot_slots
        )
        rot_list = rot_list_picked[:rot_slots]
        if len(rot_list_all) > len(rot_list):
            info_limits.append(f"Aktien-Limit aktiv: Rotation wurde profil-basiert auf **{rot_slots}** Aktien gepickt (Max Aktien {max_aktien_int}).")

    # ETF-Raten
    raw_weights = {etf: etf_weight_for(etf) for etf in etf_list}
    total_w = sum(raw_weights.values())
    etf_raten = {}
    if etf_list:
        if total_w > 0:
            for etf, w in raw_weights.items():
                etf_raten[etf] = etf_budget * (w / total_w)
        else:
            equal = etf_budget / len(etf_list)
            for etf in etf_list:
                etf_raten[etf] = equal

    # Favoriten/Rotation: Anzahl pro Monat
    favs_pro_monat_eff = min(favs_pro_monat, len(fav_list)) if fav_list else 0
    rot_per_month_user = max(0, anzahl_aktien_pro_monat - favs_pro_monat_eff)
    if not rot_list:
        rot_per_month_user = 0

    rot_per_month_eff = rot_per_month_user

    # Multiplikatorverteilung
    fav_count = favs_pro_monat_eff
    rot_count = rot_per_month_eff

    if rot_count == 0 and fav_count > 0:
        rot_rate = 0.0
        fav_rate_per_fav = aktien_budget / fav_count
        info_adjustments.append("Keine Rotation möglich → gesamtes Aktienbudget geht in Favoriten.")
    elif fav_count == 0 and rot_count > 0:
        fav_rate_per_fav = 0.0
        rot_rate = aktien_budget / rot_count
    elif fav_count == 0 and rot_count == 0:
        fav_rate_per_fav = 0.0
        rot_rate = 0.0
        info_adjustments.append("Keine Aktien ausgewählt (Favoriten/Rotation leer).")
    else:
        denom = (rot_count * 1.0) + (fav_count * float(fav_multiplier))
        rot_rate = aktien_budget / denom if denom > 0 else 0.0
        fav_rate_per_fav = rot_rate * float(fav_multiplier)

    # Mindestbetrag Rotation prüfen
    if rot_per_month_eff > 0 and min_rate_rotation > 0 and rot_rate < min_rate_rotation:
        while rot_per_month_eff > 0:
            denom = (rot_per_month_eff * 1.0) + (fav_count * float(fav_multiplier))
            candidate_rot_rate = aktien_budget / denom if denom > 0 else 0.0
            if candidate_rot_rate >= min_rate_rotation:
                rot_rate = candidate_rot_rate
                fav_rate_per_fav = rot_rate * float(fav_multiplier)
                break
            rot_per_month_eff -= 1

        info_adjustments.append(
            f"Rotation-Aktien/Monat reduziert, damit mind. {min_rate_rotation:.2f}€ pro Rotation-Aktie erreicht werden."
        )

        if rot_per_month_eff == 0 and fav_count > 0:
            rot_rate = 0.0
            fav_rate_per_fav = aktien_budget / fav_count
            info_adjustments.append("Rotation fiel auf 0 → gesamtes Aktienbudget geht in Favoriten.")

    # Rotation Pool Reihenfolge: Ausgewogen optional shuffle
    rot_list_effective = rot_list[:]
    if profil == "Ausgewogen (Standard)" and shuffle_rotation and len(rot_list_effective) > 1:
        seed = profile_seed(profil) if auswahl_wiederholbar else None
        random.seed(seed)
        random.shuffle(rot_list_effective)

    # Trefferquote
    if rot_list_effective:
        scored_ui = [(score_rotation(s, profil), s) for s in rot_list_effective]
        hits = sum(1 for sc, _ in scored_ui if sc > 0)
        pct = (hits / len(rot_list_effective) * 100) if rot_list_effective else 0.0
    else:
        hits, pct = 0, 0.0

    # Rotation Subset nach Slots (Zeitfenster)
    slots_rot_total = int(monate) * int(rot_per_month_eff)
    if begrenze_rotation and rot_per_month_eff > 0 and len(rot_list_effective) > slots_rot_total:
        dropped = len(rot_list_effective) - slots_rot_total
        rot_list_effective = rot_list_effective[:slots_rot_total]
        info_adjustments.append(
            f"Rotation gekürzt: {len(rot_list)} im Pool, aber nur {slots_rot_total} Rotation-Slots "
            f"({monate}×{rot_per_month_eff}) → {dropped} Werte wurden nicht berücksichtigt."
        )

    # Roadmaps
    fav_roadmap, rot_roadmap = [], []
    monate_int = int(monate)

    for i in range(monate_int):
        if favs_pro_monat_eff > 0:
            start_fav = i % len(fav_list)
            favs = [fav_list[(start_fav + k) % len(fav_list)] for k in range(favs_pro_monat_eff)]
        else:
            favs = []
        fav_roadmap.append(favs)

        if rot_per_month_eff > 0 and rot_list_effective:
            start_rot = (i * rot_per_month_eff) % len(rot_list_effective)
            rot = rot_list_effective[start_rot:start_rot + rot_per_month_eff]
            if len(rot) < rot_per_month_eff and len(rot_list_effective) > 0:
                rot += rot_list_effective[0:rot_per_month_eff - len(rot)]
            rot_roadmap.append(rot)
        else:
            rot_roadmap.append([])

    # Summen aggregieren
    aktien_sum = {}
    for m in range(monate_int):
        for a in fav_roadmap[m]:
            aktien_sum[a] = aktien_sum.get(a, 0) + fav_rate_per_fav
        for a in rot_roadmap[m]:
            aktien_sum[a] = aktien_sum.get(a, 0) + rot_rate

    etf_sum = {etf: etf_raten.get(etf, 0) * monate_int for etf in etf_list}

    all_data = []
    for name, betrag in aktien_sum.items():
        typ = "Favorit" if name in fav_list else "Rotation"
        all_data.append({"Name": name, "Typ": typ, "Gesamtbetrag (€)": round(betrag, 2)})

    for name, betrag in etf_sum.items():
        all_data.append({"Name": name, "Typ": "ETF", "Gesamtbetrag (€)": round(betrag, 2)})

    df_export = pd.DataFrame(all_data)

    return {
        "monatlicher_betrag": monatlicher_betrag,
        "etf_list": etf_list,
        "etf_raten": etf_raten,
        "fav_list": fav_list,
        "rot_list_effective": rot_list_effective,
        "fav_rate_per_fav": fav_rate_per_fav,
        "rot_rate": rot_rate,
        "monate_int": monate_int,
        "fav_roadmap": fav_roadmap,
        "rot_roadmap": rot_roadmap,
        "df_export": df_export,
        "hits": hits,
        "pct": pct,
        "profil": profil,
        "profil_staerke": profil_staerke,
        "auswahl_wiederholbar": auswahl_wiederholbar,
        "info_limits": info_limits,
        "info_adjustments": info_adjustments,
        "top_n_chart": top_n_chart,
        "show_tag_table": show_tag_table,
    }

if submitted:
    try:
        res = compute_plan(
            zielsumme=st.session_state.zielsumme,
            monate=st.session_state.monate,
            aktienanteil=st.session_state.aktienanteil,
            anzahl_aktien_pro_monat=st.session_state.anzahl_aktien_pro_monat,
            favoriten_text=st.session_state.favoriten,
            rotation_text=st.session_state.rotation_aktien,
            etfs_text=st.session_state.etfs,
            max_aktien=st.session_state.max_aktien,
            max_etfs=st.session_state.max_etfs,
            begrenze_rotation=st.session_state.begrenze_rotation,
            profil=st.session_state.profil,
            profil_staerke=st.session_state.get("profil_staerke", "Strong"),
            auswahl_wiederholbar=st.session_state.auswahl_wiederholbar,
            shuffle_rotation=st.session_state.shuffle_rotation,
            favs_pro_monat=st.session_state.favs_pro_monat,
            fav_multiplier=(1.5 if st.session_state.auto_modus else st.session_state.get("fav_multiplier", 1.5)),
            min_rate_rotation=st.session_state.min_rate_rotation,
            top_n_chart=st.session_state.top_n_chart,
            show_tag_table=st.session_state.get("show_tag_table", False),
        )
        st.session_state.result = res
        st.session_state.last_info_limits = res["info_limits"]
        st.session_state.last_info_adjustments = res["info_adjustments"]
        st.success("Sparplan erfolgreich berechnet! ✅")
    except Exception as e:
        st.error(str(e))

# -----------------------------
# Render result (no re-calc needed)
# -----------------------------
res = st.session_state.result
if res is not None:
    st.divider()

    for msg in st.session_state.last_info_limits:
        st.info(msg)
    for msg in st.session_state.last_info_adjustments:
        st.info(msg)

    st.caption(
        f"Rotation-Profil **{res['profil']}** • Trefferquote: **{res['hits']}/{len(res['rot_list_effective'])}** "
        f"(**{res['pct']:.0f}%**) • Stärke: **{res['profil_staerke']}** • "
        f"{'wiederholbar' if res['auswahl_wiederholbar'] else 'jedes Mal neu'}"
    )

    with st.expander("🧩 Gepickter Rotation-Pool (2-Spalten)", expanded=False):
        render_two_col_grid(res["rot_list_effective"])

    if res["show_tag_table"] and res["rot_list_effective"]:
        rows = []
        for s in res["rot_list_effective"]:
            rows.append({
                "Name": s,
                "Tags": ", ".join(tags_for_rotation(s)),
                "Profil-Score": score_rotation(s, res["profil"])
            })
        st.subheader("Rotation-Kategorisierung")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    if res["rot_list_effective"]:
        top5 = sorted([(score_rotation(s, res["profil"]), s) for s in res["rot_list_effective"]], key=lambda t: t[0], reverse=True)[:5]
        with st.expander("🔍 Profil-Details (Top 5 Picks)", expanded=False):
            show_reason = st.checkbox("Kurzbegründung anzeigen", value=True, key="show_reason_top5")
            for i, (sc, name) in enumerate(top5, start=1):
                if show_reason:
                    reasons = ", ".join(explain_rotation(name, res["profil"]))
                    st.markdown(f"{i}. **{name}** — Score **{sc:+d}** _(Tags: {reasons})_")
                else:
                    st.markdown(f"{i}. **{name}** — Score **{sc:+d}**")

    st.subheader("Gesamtübersicht")
    st.dataframe(res["df_export"], use_container_width=True)

    csv = res["df_export"].to_csv(index=False).encode("utf-8")
    st.download_button("CSV herunterladen", data=csv, file_name="sparplan_gesamtuebersicht.csv", mime="text/csv")

    fig, ax = plt.subplots(figsize=(10, 6))
    farben = {"Favorit": "tab:green", "Rotation": "tab:orange", "ETF": "tab:blue"}

    df_sorted = res["df_export"].sort_values(by="Gesamtbetrag (€)", ascending=False)
    top_n_chart = int(res["top_n_chart"])

    rest_sum = 0.0
    if len(df_sorted) > top_n_chart:
        df_plot = df_sorted.head(top_n_chart).copy()
        rest_sum = df_sorted.iloc[top_n_chart:]["Gesamtbetrag (€)"].sum()
    else:
        df_plot = df_sorted

    farben_liste = [farben.get(t, "gray") for t in df_plot["Typ"]]
    ax.barh(df_plot["Name"], df_plot["Gesamtbetrag (€)"], color=farben_liste)
    ax.set_xlabel("Gesamtbetrag (€)")
    ax.set_title("Verteilung nach Sparplan")
    ax.invert_yaxis()

    from matplotlib.patches import Patch
    legende_farben = [
        Patch(facecolor='tab:green', label='Favorit'),
        Patch(facecolor='tab:orange', label='Rotation'),
        Patch(facecolor='tab:blue', label='ETF')
    ]
    ax.legend(handles=legende_farben, loc='lower right')
    ax.tick_params(axis='y', labelsize=8)
    plt.tight_layout()
    st.pyplot(fig)

    if rest_sum > 0:
        st.caption(f"Others (Rest): {rest_sum:,.2f} €")

    gruppe = res["df_export"].groupby("Typ")["Gesamtbetrag (€)"].sum()
    fig1, ax1 = plt.subplots()
    ax1.bar(gruppe.index, gruppe.values, color=[farben.get(t, "gray") for t in gruppe.index])
    ax1.set_title("Verteilung nach Typ")
    ax1.set_ylabel("Gesamtbetrag (€)")
    st.pyplot(fig1)

    etf_df = res["df_export"][res["df_export"]["Typ"] == "ETF"]
    if not etf_df.empty:
        fig2, ax2 = plt.subplots()
        ax2.pie(etf_df["Gesamtbetrag (€)"], labels=etf_df["Name"], autopct='%1.1f%%', startangle=140)
        ax2.set_title("ETF-Allokation")
        st.pyplot(fig2)

    st.subheader("Monatliche Raten")
    show_all = st.checkbox("Alle Monate anzeigen (lang)", value=False, key="show_all_months")

    def render_month(m_index: int):
        st.markdown(f"**Monat {m_index + 1} – Aktien**")
        for a in res["fav_roadmap"][m_index]:
            st.markdown(f"**{a}**: {res['fav_rate_per_fav']:.2f} €")
        for a in res["rot_roadmap"][m_index]:
            st.markdown(f"{a}: {res['rot_rate']:.2f} €")

        st.markdown("**ETFs**")
        for e in res["etf_list"]:
            st.markdown(f"**{e}**: {res['etf_raten'].get(e, 0):.2f} €")

    if show_all:
        for m in range(res["monate_int"]):
            with st.expander(f"Monat {m + 1} anzeigen", expanded=False):
                render_month(m)
    else:
        month_choice = st.selectbox(
            "Monat auswählen",
            options=list(range(1, res["monate_int"] + 1)),
            index=0,
            key="month_choice"
        )
        with st.expander("Details anzeigen", expanded=True):
            render_month(month_choice - 1)