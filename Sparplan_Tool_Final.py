import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
import random
from typing import Optional, Dict, Any, List

st.set_page_config(page_title="Dynamischer Sparplan-Rechner", layout="wide")

# -----------------------------
# Session State (Cache)
# -----------------------------
if "calc_done" not in st.session_state:
    st.session_state.calc_done = False
if "results" not in st.session_state:
    st.session_state.results = {}
if "last_inputs_sig" not in st.session_state:
    st.session_state.last_inputs_sig = None

# -----------------------------
# Logo und Branding
# -----------------------------
from PIL import Image
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
def clean_lines(text: str) -> List[str]:
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

def pick_etfs(etf_list: List[str], max_count: int) -> List[str]:
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

def render_two_col_grid(title: str, items: List[str]):
    st.subheader(title)
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
# Tagging: ALLE Rotation-Aktien bekommen Tags
# -----------------------------
ALL_TAGS = {
    # Tech / AI
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

    # Growth / Platform
    "Platform/Consumer": [
        "Airbnb (A)","Netflix","Spotify Technology","Shopify (A)","MercadoLibre","Take-Two Interactive",
        "Alibaba Group (ADR)","Amazon.com","Apple","Tencent Holdings","Xiaomi"
    ],
    "EV/Auto": [
        "Tesla","BYD","Nio","BMW","Mercedes-Benz Group"
    ],

    # Value / Dividend / Quality
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

    # Industrials / Materials / Energy / Defense
    "Industrials": [
        "Siemens","Siemens Energy","Cummins","Schaeffler","ThyssenKrupp","TKMS AG & Co. KGaA Inhaber-…",
        "Nordex","Constellation Energy","RENK Group","Adyen"
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

    # Real Estate
    "REIT": [
        "Realty Income"
    ],

    # Special / Misc
    "Carbon/ESG": [
        "Aker Carbon Capture"
    ],
    "Luxury": [
        "LVMH Louis Vuitton Moet Hen…"
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
    x = x.replace("…", "...")  # falls
    x = re.sub(r"\(a\)|\(b\)", "", x)
    x = x.replace("adr", "")
    x = re.sub(r"[^a-z0-9\s\.\-&]", "", x)
    x = re.sub(r"\s+", " ", x).strip()
    return x

_TAG_LOOKUP: Dict[str, set] = {}
for tag, names in ALL_TAGS.items():
    for n in names:
        _TAG_LOOKUP.setdefault(normalize_name(n), set()).add(tag)

_RISK_LOOKUP: Dict[str, set] = {}
for tag, names in RISK_TAGS.items():
    for n in names:
        _RISK_LOOKUP.setdefault(normalize_name(n), set()).add(tag)

def tags_for_rotation(name: str) -> List[str]:
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
        if "High Volatility" in tags:
            return -1
        if "Early/Speculative" in tags:
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

def explain_rotation(name: str, profile: str) -> List[str]:
    tags = tags_for_rotation(name)
    wanted = set(PROFILE_WANTED_TAGS.get(profile, []))
    hits = [t for t in tags if t in wanted]
    if hits:
        return hits[:3]
    return tags[:2]

def pick_rotation_by_profile(
    rot_list: List[str],
    profile: str,
    strength: str,
    repeatable: bool,
    do_shuffle: bool,
    desired_pool_size: Optional[int] = None
) -> List[str]:
    """
    ✅ PICKT den Pool (nicht nur Reihenfolge)
    """
    if not rot_list:
        return []

    seed = profile_seed(profile) if repeatable else None
    random.seed(seed)

    scored = []
    for s in rot_list:
        sc = score_rotation(s, profile)
        tie = random.random()
        scored.append((sc, tie, s))

    scored.sort(key=lambda t: (-t[0], t[1]))

    if profile == "Ausgewogen (Standard)":
        ordered = [t[2] for t in scored] if do_shuffle else rot_list[:]
        return ordered[:desired_pool_size] if desired_pool_size else ordered

    positives = [t for t in scored if t[0] > 0]
    rest = [t for t in scored if t[0] <= 0]

    if strength == "Mild":
        ordered = [t[2] for t in positives] + [t[2] for t in rest]
    elif strength == "Normal":
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

# -----------------------------
# Berechnung (als Funktion)
# -----------------------------
def compute_plan(params: Dict[str, Any]) -> Dict[str, Any]:
    zielsumme = params["zielsumme"]
    monate = params["monate"]
    aktienanteil = params["aktienanteil"]
    anzahl_aktien_pro_monat = params["anzahl_aktien_pro_monat"]
    favoriten_text = params["favoriten_text"]
    rotation_text = params["rotation_text"]
    etfs_text = params["etfs_text"]

    einfach_modus = params["einfach_modus"]
    max_aktien = params["max_aktien"]
    max_etfs = params["max_etfs"]
    begrenze_rotation = params["begrenze_rotation"]
    profil = params["profil"]
    auswahl_wiederholbar = params["auswahl_wiederholbar"]
    shuffle_rotation = params["shuffle_rotation"]
    profil_staerke = params["profil_staerke"]
    show_tag_table = params["show_tag_table"]

    favs_pro_monat = params["favs_pro_monat"]
    fav_multiplier = params["fav_multiplier"]
    min_rate_rotation = params["min_rate_rotation"]
    top_n_chart = params["top_n_chart"]

    # Guard
    if not monate or monate <= 0:
        raise ValueError("Die Dauer (Monate) muss größer als 0 sein.")

    etf_anteil = 100 - aktienanteil

    fav_list_raw = clean_lines(favoriten_text)
    rot_list_raw = clean_lines(rotation_text)
    etf_list_raw = clean_lines(etfs_text)

    # Wenn keine ETFs, dann 100% Aktien
    if not etf_list_raw:
        aktienanteil = 100
        etf_anteil = 0

    monatlicher_betrag = zielsumme / monate
    aktien_budget = monatlicher_betrag * aktienanteil / 100
    etf_budget = monatlicher_betrag * etf_anteil / 100

    info_limits = []
    info_adjustments = []

    # ETFs limitieren
    etf_list = pick_etfs(etf_list_raw, int(max_etfs)) if etf_list_raw else []
    if len(etf_list_raw) > len(etf_list):
        info_limits.append(f"ETF-Limit aktiv: {len(etf_list_raw)} eingegeben → **{len(etf_list)}** werden verwendet.")

    # Aktien-Limit: Rotation profilbasiert picken
    fav_list = fav_list_raw[:]
    rot_list_all = rot_list_raw[:]
    max_aktien_int = int(max_aktien)

    if len(fav_list) > max_aktien_int:
        fav_list = fav_list[:max_aktien_int]
        rot_list = []
        info_limits.append(
            f"Aktien-Limit: Favoriten > Max. Aktien → Favoriten auf {max_aktien_int} gekürzt, Rotation deaktiviert."
        )
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
            info_limits.append(
                f"Aktien-Limit aktiv: Rotation wurde profil-basiert auf **{rot_slots}** Aktien gepickt (Max Aktien {max_aktien_int})."
            )

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

    # Multiplikator-Logik
    fav_count = favs_pro_monat_eff
    rot_count = rot_per_month_eff

    if rot_count == 0 and fav_count > 0:
        rot_rate = 0.0
        fav_rate_per_fav = aktien_budget / fav_count
        info_adjustments.append("Keine Rotation möglich -> gesamtes Aktienbudget geht in Favoriten.")
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
            info_adjustments.append("Rotation fiel auf 0 -> gesamtes Aktienbudget geht in Favoriten.")

    # Rotation Pool Reihenfolge (Ausgewogen extra shuffle)
    rot_list_effective = rot_list[:]
    if profil == "Ausgewogen (Standard)" and shuffle_rotation and len(rot_list_effective) > 1:
        seed = profile_seed(profil) if auswahl_wiederholbar else None
        random.seed(seed)
        random.shuffle(rot_list_effective)

    # Trefferquote
    hits = 0
    pct = 0.0
    if rot_list_effective:
        scored_ui = [(score_rotation(s, profil), s) for s in rot_list_effective]
        hits = sum(1 for sc, _ in scored_ui if sc > 0)
        pct = (hits / len(rot_list_effective) * 100)

    # Tag Table
    tag_table_df = None
    if rot_list_effective and show_tag_table:
        rows = []
        for s in rot_list_effective:
            rows.append({
                "Name": s,
                "Tags": ", ".join(tags_for_rotation(s)),
                "Profil-Score": score_rotation(s, profil)
            })
        tag_table_df = pd.DataFrame(rows)

    # Top 5
    top5 = []
    if rot_list_effective:
        top5 = sorted([(score_rotation(s, profil), s) for s in rot_list_effective], key=lambda t: t[0], reverse=True)[:5]

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

    # Export
    all_data = []
    for name, betrag in aktien_sum.items():
        typ = "Favorit" if name in fav_list else "Rotation"
        all_data.append({"Name": name, "Typ": typ, "Gesamtbetrag (€)": round(betrag, 2)})

    for name, betrag in etf_sum.items():
        all_data.append({"Name": name, "Typ": "ETF", "Gesamtbetrag (€)": round(betrag, 2)})

    df_export = pd.DataFrame(all_data)

    # Chart Prep
    farben = {"Favorit": "tab:green", "Rotation": "tab:orange", "ETF": "tab:blue"}
    df_sorted = df_export.sort_values(by="Gesamtbetrag (€)", ascending=False)

    rest_sum = 0.0
    if len(df_sorted) > top_n_chart:
        df_plot = df_sorted.head(top_n_chart).copy()
        rest_sum = df_sorted.iloc[top_n_chart:]["Gesamtbetrag (€)"].sum()
    else:
        df_plot = df_sorted

    # Typ Chart Data
    gruppe = df_export.groupby("Typ")["Gesamtbetrag (€)"].sum()
    etf_df = df_export[df_export["Typ"] == "ETF"]

    return {
        # inputs echo
        "zielsumme": zielsumme,
        "monate_int": monate_int,
        "aktienanteil": aktienanteil,
        "etf_anteil": etf_anteil,
        "monatlicher_betrag": monatlicher_betrag,
        # plan objects
        "fav_list": fav_list,
        "rot_pool": rot_list,                 # gepickter Pool (vor Zeitfenster-Cut)
        "rot_list_effective": rot_list_effective,  # effective für Roadmap (ggf. nach slots gekürzt)
        "etf_list": etf_list,
        "etf_raten": etf_raten,
        "fav_roadmap": fav_roadmap,
        "rot_roadmap": rot_roadmap,
        "fav_rate_per_fav": fav_rate_per_fav,
        "rot_rate": rot_rate,
        "df_export": df_export,
        # profile UI
        "hits": hits,
        "pct": pct,
        "top5": top5,
        "tag_table_df": tag_table_df,
        # infos
        "info_limits": info_limits,
        "info_adjustments": info_adjustments,
        "rest_sum": rest_sum,
        # chart data
        "farben": farben,
        "df_plot": df_plot,
        "df_sorted": df_sorted,
        "gruppe": gruppe,
        "etf_df": etf_df,
        # misc
        "profil": profil,
        "profil_staerke": profil_staerke,
        "auswahl_wiederholbar": auswahl_wiederholbar,
    }

# -----------------------------
# UI: Alles als Form -> keine "Neuberechnung" bei Anzeige-Klicks
# -----------------------------
with st.form("inputs_form", clear_on_submit=False):
    st.subheader("Eingaben")

    zielsumme = st.number_input("Zielsumme (€)", value=50000, key="in_zielsumme")
    monate = st.number_input("Dauer (Monate)", value=100, key="in_monate")
    aktienanteil = st.slider("Aktienanteil (%)", 0, 100, 65, key="in_aktienanteil")
    etf_anteil_preview = 100 - aktienanteil

    st.markdown(f"**ETFs erhalten {etf_anteil_preview} %, Aktien erhalten {aktienanteil} %**")
    monatlicher_betrag_preview = zielsumme / monate if monate else 0
    st.markdown(f"### Monatlicher Sparbetrag: {monatlicher_betrag_preview:.2f} €")

    anzahl_aktien_pro_monat = st.number_input(
        "Wie viele Aktien pro Monat besparen?",
        min_value=3,
        max_value=15,
        value=7,
        key="in_anzahl_aktien_pro_monat"
    )

    st.caption("Favoriten werden pro Aktie stärker bespart als Rotation. Rotation-Aktien werden automatisch ergänzt.")

    favoriten = st.text_area("Favoritenaktien (eine pro Zeile)", value=default_favoriten, key="in_favoriten")
    st.caption("Falls keine Favoriten angegeben sind, wird das gesamte Aktienbudget auf rotierende Aktien verteilt.")

    rotation_aktien = st.text_area("Weitere Aktien (eine pro Zeile)", value=default_aktien, key="in_rotation")
    etfs = st.text_area("ETFs (eine pro Zeile)", value=default_etfs, key="in_etfs")
    st.caption("Falls keine ETFs angegeben sind, wird das gesamte Kapital auf Aktien verteilt.")

    st.subheader("⚙️ Erweiterte Einstellungen")
    einfach_modus = st.checkbox(
        "Einfach-Modus (empfohlen für Anfänger): begrenzt die Anzahl der Positionen automatisch",
        value=True,
        key="in_einfach"
    )

    max_aktien = 40
    max_etfs = 10
    if einfach_modus:
        st.caption("Einfach-Modus aktiv: Max. **40 Aktien** (inkl. Favoriten) und **10 ETFs**.")
    else:
        max_aktien = st.number_input("Max. Aktien im Plan (inkl. Favoriten)", min_value=5, max_value=200, value=40, step=1, key="in_max_aktien")
        max_etfs = st.number_input("Max. ETFs im Plan", min_value=1, max_value=50, value=10, step=1, key="in_max_etfs")

    begrenze_rotation = st.checkbox(
        "Rotation-Liste automatisch kürzen (nur so viele, wie im Zeitraum bespart werden können)",
        value=True,
        key="in_begrenze_rotation"
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
        index=0,
        key="in_profil"
    )

    auswahl_wiederholbar = st.checkbox(
        "Auswahl wiederholbar (gleiches Profil + gleiche Inputs = gleiche Reihenfolge)",
        value=True,
        key="in_repeatable"
    )

    shuffle_rotation = st.checkbox(
        "Rotation mischen (empfohlen – verhindert Alphabet-Reihenfolge)",
        value=True,
        key="in_shuffle_rotation"
    )

    with st.expander("🔧 Advanced (optional)"):
        profil_staerke = st.selectbox(
            "Profil-Stärke (wie stark das Profil die Rotation beeinflusst)",
            options=["Mild", "Normal", "Strong"],
            index=2,
            key="in_profil_staerke"
        )
        show_tag_table = st.checkbox("Rotation-Kategorisierung anzeigen (Tabelle)", value=False, key="in_show_tag_table")
        st.caption("Mild = wenig Filter • Strong = harter Filter (Fallback wenn zu wenige Treffer)")

    favs_pro_monat = st.slider("Wie viele Favoriten pro Monat besparen?", 1, 3, 2, key="in_favs_pro_monat")

    auto_modus = st.checkbox(
        "Auto-Modus: Favoriten-Multiplikator fix (empfohlen für Anfänger)",
        value=True,
        key="in_auto_modus"
    )

    min_rate_rotation = st.number_input(
        "Mindestbetrag pro Rotation-Aktie (€/Monat) – falls nötig wird die Anzahl Rotation-Aktien pro Monat automatisch reduziert",
        min_value=0.0,
        value=20.0,
        step=1.0,
        key="in_min_rate_rotation"
    )

    FAV_MULTIPLIER_AUTO = 1.5
    if auto_modus:
        fav_multiplier = FAV_MULTIPLIER_AUTO
        st.caption(f"Auto-Modus aktiv: Favoriten werden pro Aktie mit **{fav_multiplier:.2f}x** gegenüber Rotation gewichtet.")
    else:
        fav_multiplier = st.slider(
            "Favoriten stärker besparen als Rotation (pro Aktie, Multiplikator)",
            min_value=1.0,
            max_value=3.0,
            value=1.5,
            step=0.1,
            key="in_fav_multiplier"
        )

    top_n_chart = st.slider("Diagramm: Anzahl angezeigter Positionen", 10, 120, 40, key="in_top_n_chart")

    submitted = st.form_submit_button("Sparplan berechnen")

# -----------------------------
# Submit -> rechnen + cachen
# -----------------------------
if submitted:
    params = {
        "zielsumme": zielsumme,
        "monate": monate,
        "aktienanteil": aktienanteil,
        "anzahl_aktien_pro_monat": anzahl_aktien_pro_monat,
        "favoriten_text": favoriten,
        "rotation_text": rotation_aktien,
        "etfs_text": etfs,
        "einfach_modus": einfach_modus,
        "max_aktien": max_aktien,
        "max_etfs": max_etfs,
        "begrenze_rotation": begrenze_rotation,
        "profil": profil,
        "auswahl_wiederholbar": auswahl_wiederholbar,
        "shuffle_rotation": shuffle_rotation,
        "profil_staerke": profil_staerke,
        "show_tag_table": show_tag_table,
        "favs_pro_monat": favs_pro_monat,
        "fav_multiplier": fav_multiplier,
        "min_rate_rotation": min_rate_rotation,
        "top_n_chart": top_n_chart,
    }

    # simple inputs signature (für optionales debugging)
    sig = str(params)

    try:
        res = compute_plan(params)
        st.session_state.results = res
        st.session_state.calc_done = True
        st.session_state.last_inputs_sig = sig
        st.success("Sparplan erfolgreich berechnet!")
    except Exception as e:
        st.session_state.calc_done = False
        st.error(str(e))

# -----------------------------
# Anzeige: basiert nur auf Cache (wird NICHT "leer" bei UI-Interaktion)
# -----------------------------
if st.session_state.calc_done:
    R = st.session_state.results

    # Infos
    if R.get("info_limits"):
        for msg in R["info_limits"]:
            st.info(msg)
    if R.get("info_adjustments"):
        for msg in R["info_adjustments"]:
            st.info(msg)

    # Trefferquote + Pool
    if R.get("rot_pool") is not None:
        rot_pool = R["rot_pool"]
        hits = R.get("hits", 0)
        pct = R.get("pct", 0.0)
        st.caption(
            f"Rotation-Profil **{R['profil']}** • Trefferquote: **{hits}/{len(rot_pool)}** (**{pct:.0f}%**) "
            f"• Stärke: **{R['profil_staerke']}** • "
            f"{'wiederholbar' if R['auswahl_wiederholbar'] else 'jedes Mal neu'}"
        )
        with st.expander("🧩 Gepickter Rotation-Pool (2-Spalten)", expanded=True):
            render_two_col_grid("Rotation-Pool", rot_pool)

    # Tag Table
    if R.get("tag_table_df") is not None:
        st.subheader("Rotation-Kategorisierung")
        st.dataframe(R["tag_table_df"])

    # Top 5
    if R.get("top5"):
        with st.expander("🔍 Profil-Details (Top 5 Picks)", expanded=False):
            show_reason = st.checkbox("Kurzbegründung anzeigen", value=True, key="ui_show_reason")
            st.markdown(f"**Profil:** {R['profil']}  •  **Stärke:** {R['profil_staerke']}")
            for i, (sc, name) in enumerate(R["top5"], start=1):
                if show_reason:
                    reasons = ", ".join(explain_rotation(name, R["profil"]))
                    st.markdown(f"{i}. **{name}** — Score **{sc:+d}** _(Tags: {reasons})_")
                else:
                    st.markdown(f"{i}. **{name}** — Score **{sc:+d}**")
            st.caption("Hinweis: Das ist ein Sortier-/Auswahl-Mechanismus, kein Qualitäts-Ranking.")

    # Gesamtübersicht
    st.subheader("Gesamtübersicht")
    st.dataframe(R["df_export"])

    csv = R["df_export"].to_csv(index=False).encode("utf-8")
    st.download_button(
        "CSV herunterladen",
        data=csv,
        file_name="sparplan_gesamtuebersicht.csv",
        mime="text/csv",
        key="ui_dl_csv"
    )

    # Chart: Verteilung nach Sparplan (Top-N)
    fig, ax = plt.subplots(figsize=(10, 6))
    farben = R["farben"]
    df_plot = R["df_plot"]

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

    if R.get("rest_sum", 0) > 0:
        st.caption(f"Others (Rest): {R['rest_sum']:,.2f} €")

    # Typ Chart
    gruppe = R["gruppe"]
    fig1, ax1 = plt.subplots()
    ax1.bar(gruppe.index, gruppe.values, color=[farben.get(t, "gray") for t in gruppe.index])
    ax1.set_title("Verteilung nach Typ")
    ax1.set_ylabel("Gesamtbetrag (€)")
    st.pyplot(fig1)

    # ETF Pie
    etf_df = R["etf_df"]
    if not etf_df.empty:
        fig2, ax2 = plt.subplots()
        ax2.pie(etf_df["Gesamtbetrag (€)"], labels=etf_df["Name"], autopct='%1.1f%%', startangle=140)
        ax2.set_title("ETF-Allokation")
        st.pyplot(fig2)

    # Depotwachstum
    with st.expander("📈 Depotwachstum simulieren"):
        st.markdown("Vereinfachte Simulation mit konstanter Rendite (ohne Gebühren/Steuern).")

        fig, ax = plt.subplots()
        renditen = {
            "Underperform (4%)": 0.04,
            "Default (8%)": 0.08,
            "Overperform (20%)": 0.20,
            "Godmode (50%)": 0.50
        }

        monate_int = R["monate_int"]
        monatlicher_betrag = R["monatlicher_betrag"]

        for label, rate in renditen.items():
            depotwert = []
            gesamt = 0
            for _ in range(monate_int):
                gesamt = (gesamt + monatlicher_betrag) * (1 + rate / 12)
                depotwert.append(gesamt)
            ax.plot(range(1, monate_int + 1), depotwert, label=label)

        ax.set_title("Depotwachstum simulieren")
        ax.set_xlabel("Monat")
        ax.set_ylabel("Depotwert (€)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    # Monatliche Raten (UI-Interaktion ohne "Reset" dank Session Cache + stabile keys)
    st.subheader("Monatliche Raten")

    show_all = st.checkbox("Alle Monate anzeigen (lang)", value=False, key="ui_show_all_months")

    def render_month(idx: int):
        st.markdown(f"**Monat {idx + 1} – Aktien**")

        for a in R["fav_roadmap"][idx]:
            st.markdown(f"**{a}**: {R['fav_rate_per_fav']:.2f} €")

        for a in R["rot_roadmap"][idx]:
            st.markdown(f"{a}: {R['rot_rate']:.2f} €")

        st.markdown("**ETFs**")
        for e in R["etf_list"]:
            st.markdown(f"**{e}**: {R['etf_raten'].get(e, 0):.2f} €")

    if show_all:
        for m in range(R["monate_int"]):
            with st.expander(f"Monat {m + 1} anzeigen", expanded=False):
                render_month(m)
    else:
        month_choice = st.selectbox(
            "Monat auswählen",
            options=list(range(1, R["monate_int"] + 1)),
            index=0,
            key="ui_month_choice"
        )
        with st.expander("Details anzeigen", expanded=True):
            render_month(month_choice - 1)

else:
    st.info("Noch nichts berechnet – bitte oben im Formular auf **Sparplan berechnen** klicken.")