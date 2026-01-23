import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dynamischer Sparplan-Rechner", layout="wide")

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
# Eingaben (Basics)
# -----------------------------
zielsumme = st.number_input("Zielsumme (€)", value=12000)
monate = st.number_input("Dauer (Monate)", value=24)
aktienanteil = st.slider("Aktienanteil (%)", 0, 100, 80)
etf_anteil = 100 - aktienanteil

monatlicher_betrag = zielsumme / monate if monate else 0
aktien_budget = monatlicher_betrag * aktienanteil / 100
etf_budget = monatlicher_betrag * etf_anteil / 100

st.markdown(f"**ETFs erhalten {etf_anteil} %, Aktien erhalten {aktienanteil} %**")
st.markdown(f"### Monatlicher Sparbetrag: {monatlicher_betrag:.2f} €")

anzahl_aktien_pro_monat = st.number_input(
    "Wie viele Aktien pro Monat besparen?",
    min_value=3,
    max_value=30,
    value=8
)

st.caption(
    "Favoriten werden pro Aktie stärker bespart als Rotation. "
    "Rotation-Aktien werden automatisch ergänzt."
)

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

favoriten = st.text_area("Favoritenaktien (eine pro Zeile)", value=default_favoriten)
st.caption("Falls keine Favoriten angegeben sind, wird das gesamte Aktienbudget auf rotierende Aktien verteilt.")

rotation_aktien = st.text_area("Weitere Aktien (eine pro Zeile)", value=default_aktien)
etfs = st.text_area("ETFs (eine pro Zeile)", value=default_etfs)
st.caption("Falls keine ETFs angegeben sind, wird das gesamte Kapital auf Aktien verteilt.")

# -----------------------------
# Erweiterte Einstellungen
# -----------------------------
st.subheader("⚙️ Erweiterte Einstellungen")

einfach_modus = st.checkbox(
    "Einfach-Modus (empfohlen für Anfänger): begrenzt die Anzahl der Positionen automatisch",
    value=True
)

max_aktien = 25
max_etfs = 5
if einfach_modus:
    st.caption(
        "Einfach-Modus aktiv: Max. **25 Aktien** (inkl. Favoriten) und **5 ETFs**. "
        "Wenn du mehr eingibst, wird eine Teilmenge ausgewählt."
    )
else:
    max_aktien = st.number_input("Max. Aktien im Plan (inkl. Favoriten)", min_value=5, max_value=200, value=25, step=1)
    max_etfs = st.number_input("Max. ETFs im Plan", min_value=1, max_value=50, value=5, step=1)

begrenze_rotation = st.checkbox(
    "Rotation-Liste automatisch kürzen (nur so viele, wie im Zeitraum bespart werden können)",
    value=True
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
    index=0
)

auswahl_wiederholbar = st.checkbox(
    "Auswahl wiederholbar (gleiches Profil + gleiche Inputs = gleiche Reihenfolge)",
    value=True
)

shuffle_rotation = st.checkbox(
    "Rotation mischen (empfohlen – verhindert Alphabet-Reihenfolge)",
    value=True
)

# ✅ Advanced (optional)
with st.expander("🔧 Advanced (optional)"):
    profil_staerke = st.selectbox(
        "Profil-Stärke (wie stark das Profil die Rotation beeinflusst)",
        options=["Mild", "Normal", "Strong"],
        index=1
    )
    st.caption("Mild = mehr Zufall/Ausgewogenheit • Strong = Profil dominiert stärker")

favs_pro_monat = st.slider("Wie viele Favoriten pro Monat besparen?", 1, 3, 2)

auto_modus = st.checkbox(
    "Auto-Modus: Favoriten-Multiplikator fix (empfohlen für Anfänger)",
    value=True
)

min_rate_rotation = st.number_input(
    "Mindestbetrag pro Rotation-Aktie (€/Monat) – falls nötig wird die Anzahl Rotation-Aktien pro Monat automatisch reduziert",
    min_value=0.0,
    value=20.0,
    step=1.0
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
        step=0.1
    )

top_n_chart = st.slider("Diagramm: Anzahl angezeigter Positionen", 10, 120, 40)

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
        "Ausgewogen (Standard)": 42,
        "Tech & AI": 1337,
        "Wachstum": 2024,
        "Dividenden & Value": 777,
        "Konservativ & defensiv": 99
    }
    return mapping.get(profile, 42)

def strength_factor(level: str) -> int:
    return {"Mild": 1, "Normal": 2, "Strong": 3}.get(level, 2)

# Keyword Sets (einfach & robust, ohne externe Daten)
TECH_BOOST = [
    "nvidia", "amd", "asml", "tsmc", "micron", "intel", "infineon", "sk hynix",
    "cloudflare", "crowdstrike", "palantir", "datadog", "servicenow", "snowflake",
    "oracle", "microsoft", "meta", "alphabet", "tesla", "xiaomi",
    "quantum", "d-wave", "ai", "robot", "drone", "chip", "semi", "semicon", "cyber"
]
GROWTH_BOOST = [
    "shopify", "airbnb", "mercado", "netflix", "tesla", "byd", "xiaomi",
    "palantir", "cloudflare", "datadog", "servicenow", "snowflake",
    "drone", "quantum", "d-wave", "intellia", "illumina"
]
VALUE_DIV_BOOST = [
    "procter", "johnson", "realty income", "berkshire", "deutsche telekom",
    "bmw", "mercedes", "siemens", "sap", "lvmh", "cummins", "evonik",
    "heidelberg", "saab", "thales", "covestro"
]
DEFENSIVE_BOOST = [
    "deutsche telekom", "johnson", "procter", "berkshire", "realty income",
    "siemens", "sap", "novo nordisk", "eli lilly", "constellation"
]
RISKY_PENALTY = [
    "coinbase", "microstrategy", "bitmine", "quantum", "d-wave", "nio", "ondas",
    "drone", "digindex"
]

def contains_any(n: str, keywords) -> bool:
    return any(k in n for k in keywords)

def score_rotation(name: str, profile: str) -> int:
    n = name.lower()
    score = 0

    if profile == "Tech & AI":
        if contains_any(n, TECH_BOOST):
            score += 3
        if contains_any(n, VALUE_DIV_BOOST):
            score -= 1

    elif profile == "Wachstum":
        if contains_any(n, GROWTH_BOOST):
            score += 3
        if contains_any(n, DEFENSIVE_BOOST):
            score -= 1

    elif profile == "Dividenden & Value":
        if contains_any(n, VALUE_DIV_BOOST):
            score += 3
        if contains_any(n, RISKY_PENALTY):
            score -= 2

    elif profile == "Konservativ & defensiv":
        if contains_any(n, DEFENSIVE_BOOST):
            score += 3
        if contains_any(n, RISKY_PENALTY):
            score -= 4
        if contains_any(n, TECH_BOOST):
            score -= 1

    else:  # Ausgewogen
        if contains_any(n, RISKY_PENALTY):
            score -= 1

    return score

def explain_rotation(name: str, profile: str):
    """Kurze, verständliche Begründung für Top Picks."""
    n = name.lower()
    reasons = []

    if profile == "Tech & AI":
        if contains_any(n, TECH_BOOST):
            reasons.append("Tech/AI")
        if "cyber" in n or "crowdstrike" in n:
            reasons.append("Cyber")
        if "cloud" in n or "cloudflare" in n:
            reasons.append("Cloud")
        if "chip" in n or "semi" in n or "asml" in n or "tsmc" in n or "amd" in n or "nvidia" in n:
            reasons.append("Semis")

    elif profile == "Wachstum":
        if contains_any(n, GROWTH_BOOST):
            reasons.append("Growth")
        if "shopify" in n or "airbnb" in n or "netflix" in n:
            reasons.append("Consumer/Platform")
        if "intellia" in n or "illumina" in n:
            reasons.append("Biotech")

    elif profile == "Dividenden & Value":
        if contains_any(n, VALUE_DIV_BOOST):
            reasons.append("Value/Dividend")
        if "realty income" in n:
            reasons.append("REIT")
        if "berkshire" in n:
            reasons.append("Holding")

    elif profile == "Konservativ & defensiv":
        if contains_any(n, DEFENSIVE_BOOST):
            reasons.append("Defensiv")
        if "deutsche telekom" in n:
            reasons.append("Telekom")
        if "johnson" in n or "procter" in n:
            reasons.append("Staples/Healthcare")
        if "berkshire" in n:
            reasons.append("Holding")

    # Fallback
    if not reasons:
        reasons = ["Profil-Score"]

    # Dedupe, max 3 Gründe
    out = []
    for r in reasons:
        if r not in out:
            out.append(r)
    return out[:3]

# -----------------------------
# Berechnung
# -----------------------------
if st.button("Sparplan berechnen"):

    fav_list_raw = clean_lines(favoriten)
    rot_list_raw = clean_lines(rotation_aktien)
    etf_list_raw = clean_lines(etfs)

    if not monate or monate <= 0:
        st.error("Die Dauer (Monate) muss größer als 0 sein.")
        st.stop()

    if not etf_list_raw:
        aktienanteil = 100
        etf_anteil = 0

    monatlicher_betrag = zielsumme / monate
    aktien_budget = monatlicher_betrag * aktienanteil / 100
    etf_budget = monatlicher_betrag * etf_anteil / 100

    info_limits = []

    # ETFs limitieren
    etf_list = pick_etfs(etf_list_raw, int(max_etfs)) if etf_list_raw else []
    if len(etf_list_raw) > len(etf_list):
        info_limits.append(f"ETF-Limit aktiv: {len(etf_list_raw)} eingegeben → **{len(etf_list)}** werden verwendet.")

    # Aktien limitieren (Favoriten zuerst)
    fav_list = fav_list_raw[:]
    rot_list = rot_list_raw[:]
    max_aktien_int = int(max_aktien)

    if len(fav_list) > max_aktien_int:
        fav_list = fav_list[:max_aktien_int]
        rot_list = []
        info_limits.append(f"Aktien-Limit: Favoriten > Max. Aktien → Favoriten auf {max_aktien_int} gekürzt, Rotation deaktiviert.")
    else:
        rot_slots = max_aktien_int - len(fav_list)
        if rot_slots < len(rot_list):
            rot_list = rot_list[:rot_slots]
            info_limits.append(f"Aktien-Limit aktiv: Rotation auf **{rot_slots}** Aktien begrenzt (Max Aktien {max_aktien_int}).")

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
    info_adjustments = []

    # -----------------------------
    # Kern-Logik Multiplikator
    # -----------------------------
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

    # -----------------------------
    # Profil-Scoring + Trefferanzeige + Top Picks
    # -----------------------------
    rot_list_effective = rot_list[:]
    prof_factor = strength_factor(profil_staerke)

    # Treffer zählen + Ranking vorbereiten (für Anzeige & sort)
    scored_for_ui = []
    hits = 0
    for s in rot_list_effective:
        base = score_rotation(s, profil)
        sc = base * prof_factor
        if sc > 0:
            hits += 1
        scored_for_ui.append((sc, s))

    if rot_list_effective:
        st.caption(f"Profil **{profil}**: {hits}/{len(rot_list_effective)} Rotation-Aktien matchen das Profil (Stärke: {profil_staerke}).")

    # ✅ Top 5 Profil-Picks (nur Erklärung/Transparenz)
    if rot_list_effective:
        top5 = sorted(scored_for_ui, key=lambda t: t[0], reverse=True)[:5]
        with st.expander("🔍 Profil-Details (Top Picks)", expanded=False):
            show_reason = st.checkbox("Kurzbegründung anzeigen", value=True)
            st.markdown(f"**Profil:** {profil}  •  **Stärke:** {profil_staerke}")
            st.markdown("**Top 5 Rotation-Picks nach Profil-Score:**")
            for i, (sc, name) in enumerate(top5, start=1):
                if show_reason:
                    reasons = ", ".join(explain_rotation(name, profil))
                    st.markdown(f"{i}. **{name}** — Score **{sc:+d}** _(Match: {reasons})_")
                else:
                    st.markdown(f"{i}. **{name}** — Score **{sc:+d}**")
            st.caption("Hinweis: Das beeinflusst nur die Reihenfolge der Rotation (kein Qualitäts-Ranking).")

    # Sort + Mix (TieBreaker)
    if rot_list_effective and shuffle_rotation:
        import random
        seed = profile_seed(profil) if auswahl_wiederholbar else None
        random.seed(seed)

        scored = []
        for s in rot_list_effective:
            sc = score_rotation(s, profil) * prof_factor
            tie = random.random()
            scored.append((sc, tie, s))

        scored.sort(key=lambda t: (-t[0], t[1]))
        rot_list_effective = [t[2] for t in scored]

    # Rotation Subset
    slots_rot_total = int(monate) * int(rot_per_month_eff)
    if begrenze_rotation and rot_per_month_eff > 0 and len(rot_list_effective) > slots_rot_total:
        dropped = len(rot_list_effective) - slots_rot_total
        rot_list_effective = rot_list_effective[:slots_rot_total]
        info_adjustments.append(
            f"Rotation gekürzt: {len(rot_list)} eingegeben, aber nur {slots_rot_total} Rotation-Slots "
            f"({monate}×{rot_per_month_eff}) → {dropped} Werte wurden nicht berücksichtigt."
        )

    # Roadmaps
    fav_roadmap, rot_roadmap = [], []
    monate_int = int(monate)

    for i in range(monate_int):
        # Favoriten
        if favs_pro_monat_eff > 0:
            start_fav = i % len(fav_list)
            favs = [fav_list[(start_fav + k) % len(fav_list)] for k in range(favs_pro_monat_eff)]
        else:
            favs = []
        fav_roadmap.append(favs)

        # Rotation
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

    # Infos
    if info_limits:
        for msg in info_limits:
            st.info(msg)

    if shuffle_rotation:
        st.caption(f"Rotation-Profil aktiv: **{profil}** {'(wiederholbar)' if auswahl_wiederholbar else '(jedes Mal neu gemischt)'}.")

    if info_adjustments:
        for msg in info_adjustments:
            st.info(msg)

    # Export
    all_data = []
    for name, betrag in aktien_sum.items():
        typ = "Favorit" if name in fav_list else "Rotation"
        all_data.append({"Name": name, "Typ": typ, "Gesamtbetrag (€)": round(betrag, 2)})

    for name, betrag in etf_sum.items():
        all_data.append({"Name": name, "Typ": "ETF", "Gesamtbetrag (€)": round(betrag, 2)})

    df_export = pd.DataFrame(all_data)

    st.subheader("Gesamtübersicht")
    st.dataframe(df_export)

    csv = df_export.to_csv(index=False).encode("utf-8")
    st.download_button("CSV herunterladen", data=csv, file_name="sparplan_gesamtuebersicht.csv", mime="text/csv")

    # Chart: Verteilung nach Sparplan (Top-N)
    fig, ax = plt.subplots(figsize=(10, 6))
    farben = {"Favorit": "tab:green", "Rotation": "tab:orange", "ETF": "tab:blue"}

    df_sorted = df_export.sort_values(by="Gesamtbetrag (€)", ascending=False)

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

    # Typ Chart
    gruppe = df_export.groupby("Typ")["Gesamtbetrag (€)"].sum()
    fig1, ax1 = plt.subplots()
    ax1.bar(gruppe.index, gruppe.values, color=[farben.get(t, "gray") for t in gruppe.index])
    ax1.set_title("Verteilung nach Typ")
    ax1.set_ylabel("Gesamtbetrag (€)")
    st.pyplot(fig1)

    # ETF Pie
    etf_df = df_export[df_export["Typ"] == "ETF"]
    if not etf_df.empty:
        fig2, ax2 = plt.subplots()
        ax2.pie(etf_df["Gesamtbetrag (€)"], labels=etf_df["Name"], autopct='%1.1f%%', startangle=140)
        ax2.set_title("ETF-Allokation")
        st.pyplot(fig2)

    st.success("Sparplan erfolgreich berechnet!")

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

        for label, rate in renditen.items():
            depotwert = []
            gesamt = 0
            for i in range(monate_int):
                gesamt = (gesamt + monatlicher_betrag) * (1 + rate / 12)
                depotwert.append(gesamt)
            ax.plot(range(1, monate_int + 1), depotwert, label=label)

        ax.set_title("Investmentwachstum mit Zinseszins")
        ax.set_xlabel("Monat")
        ax.set_ylabel("Depotwert (€)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    # Monatliche Raten
    st.subheader("Monatliche Raten")

    show_all = st.checkbox("Alle Monate anzeigen (lang)", value=False)

    def render_month(m_index: int):
        st.markdown(f"**Monat {m_index + 1} – Aktien**")

        for a in fav_roadmap[m_index]:
            st.markdown(f"**{a}**: {fav_rate_per_fav:.2f} €")

        for a in rot_roadmap[m_index]:
            st.markdown(f"{a}: {rot_rate:.2f} €")

        st.markdown("**ETFs**")
        for e in etf_list:
            st.markdown(f"**{e}**: {etf_raten.get(e, 0):.2f} €")

    if show_all:
        for m in range(monate_int):
            with st.expander(f"Monat {m + 1} anzeigen", expanded=False):
                render_month(m)
    else:
        month_choice = st.selectbox("Monat auswählen", options=list(range(1, monate_int + 1)), index=0)
        with st.expander("Details anzeigen", expanded=True):
            render_month(month_choice - 1)