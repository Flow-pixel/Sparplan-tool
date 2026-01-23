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

# ✅ Änderung: Global Dividend raus, Defence USD rein
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

# ✅ Anfänger-Preset: max Aktien 25, max ETFs 5
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

shuffle_rotation = st.checkbox(
    "Rotation zufällig mischen (empfohlen)",
    value=True
)

seed_text = st.text_input(
    "Seed (optional): gleiche Zufallsauswahl wiederholen",
    value="420"
)

# Favoriten pro Monat (Default 2)
favs_pro_monat = st.slider("Wie viele Favoriten pro Monat besparen?", 1, 3, 2)

auto_modus = st.checkbox(
    "Auto-Modus: Favoriten-Gewichtung automatisch anpassen (empfohlen für Anfänger)",
    value=True
)

# ✅ Manuell: Favoriten-Multiplikator (Default 2.0×)
fav_multiplier_manual = None
if not auto_modus:
    fav_multiplier_manual = st.slider(
        "Favoriten stärker besparen als Rotation (pro Aktie, Multiplikator)",
        min_value=1.0,
        max_value=5.0,
        value=2.0,   # ✅ DEFAULT 2x
        step=0.1
    )

min_rate_rotation = st.number_input(
    "Mindestbetrag pro Rotation-Aktie (€/Monat) – falls nötig wird die Anzahl Rotation-Aktien pro Monat automatisch reduziert",
    min_value=0.0,
    value=20.0,
    step=1.0
)

top_n_chart = st.slider("Diagramm: Anzahl angezeigter Positionen", 10, 120, 40)

# -----------------------------
# Helper
# -----------------------------
def safe_int(s: str, default: int = 420) -> int:
    try:
        return int(s.strip())
    except Exception:
        return default

def clean_lines(text: str):
    # minimale Robustheit gegen Copy/Paste Artefakte
    lines = []
    for raw in text.splitlines():
        x = raw.strip().replace("“", '"').replace("”", '"').replace("’", "'")
        x = " ".join(x.split())  # mehrfach spaces raus
        if x:
            lines.append(x)
    return lines

def auto_fav_multiplier(total_stocks_per_month: int) -> float:
    """
    Anfängerfreundlich:
    - wenige Positionen/Monat -> Favoriten stärker (bis ~3.0x)
    - viele Positionen/Monat  -> Favoriten weniger stark (bis ~1.4x)
    """
    m = 3.2 - 0.12 * total_stocks_per_month
    return max(1.4, min(3.0, m))

# ETF Gewichte (wie besprochen)
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
    """Wählt max_count ETFs: zuerst die 'wichtigen' nach Gewicht, dann rest in Eingabe-Reihenfolge."""
    if len(etf_list) <= max_count:
        return etf_list

    weights = {e: etf_weight_for(e) for e in etf_list}
    order_index = {e: i for i, e in enumerate(etf_list)}
    sorted_etfs = sorted(etf_list, key=lambda e: (-weights.get(e, 0.10), order_index.get(e, 10_000)))
    return sorted_etfs[:max_count]

def compute_rates_with_multiplier(aktien_budget_month: float, fav_count: int, rot_count: int, fav_multiplier: float):
    """
    Berechnet rot_rate und fav_rate_per_fav so, dass:
    - bei Rotation > 0 gilt: fav_rate_per_fav = rot_rate * fav_multiplier
    - Gesamtbudget wird exakt verteilt
    """
    if fav_count > 0 and rot_count > 0:
        weighted_slots = fav_count * fav_multiplier + rot_count * 1.0
        rot_rate = aktien_budget_month / weighted_slots if weighted_slots > 0 else 0.0
        fav_rate = rot_rate * fav_multiplier
        return fav_rate, rot_rate

    if fav_count > 0 and rot_count == 0:
        fav_rate = aktien_budget_month / fav_count if fav_count > 0 else 0.0
        return fav_rate, 0.0

    if fav_count == 0 and rot_count > 0:
        rot_rate = aktien_budget_month / rot_count if rot_count > 0 else 0.0
        return 0.0, rot_rate

    return 0.0, 0.0

# -----------------------------
# Berechnung
# -----------------------------
if st.button("Sparplan berechnen"):

    # Eingaben lesen + säubern
    fav_list_raw = clean_lines(favoriten)
    rot_list_raw = clean_lines(rotation_aktien)
    etf_list_raw = clean_lines(etfs)

    # Guard: Monate
    if not monate or monate <= 0:
        st.error("Die Dauer (Monate) muss größer als 0 sein.")
        st.stop()

    # Wenn keine ETFs, dann 100% Aktien
    if not etf_list_raw:
        aktienanteil = 100
        etf_anteil = 0

    monatlicher_betrag = zielsumme / monate
    aktien_budget = monatlicher_betrag * aktienanteil / 100
    etf_budget = monatlicher_betrag * etf_anteil / 100

    # -----------------------------
    # ✅ Anfänger-Limit: Max Aktien (inkl Favoriten) + Max ETFs
    # -----------------------------
    info_limits = []

    # ETFs limitieren
    etf_list = pick_etfs(etf_list_raw, int(max_etfs)) if etf_list_raw else []
    if len(etf_list_raw) > len(etf_list):
        info_limits.append(f"ETF-Limit aktiv: {len(etf_list_raw)} eingegeben → **{len(etf_list)}** werden verwendet.")

    # Aktien limitieren (Favoriten zuerst)
    fav_list = fav_list_raw[:]  # Quelle unberührt
    rot_list = rot_list_raw[:]

    max_aktien_int = int(max_aktien) if max_aktien is not None else None
    if max_aktien_int is not None:
        if len(fav_list) > max_aktien_int:
            fav_list = fav_list[:max_aktien_int]
            rot_list = []
            info_limits.append(
                f"Aktien-Limit: Favoriten waren > Max. Aktien → Favoriten wurden auf {max_aktien_int} gekürzt, Rotation deaktiviert."
            )
        else:
            rot_slots = max_aktien_int - len(fav_list)
            if rot_slots < len(rot_list):
                rot_list = rot_list[:rot_slots]
                info_limits.append(
                    f"Aktien-Limit aktiv: Rotation wurde auf **{rot_slots}** Aktien begrenzt (Max Aktien {max_aktien_int})."
                )

    # -----------------------------
    # ETF-Raten: feste Zielgewichte, dann normalisieren (falls ETFs fehlen)
    # -----------------------------
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

    # -----------------------------
    # Favoriten/Rotation: Anzahl pro Monat + Guards
    # -----------------------------
    favs_pro_monat_eff = min(favs_pro_monat, len(fav_list)) if fav_list else 0

    rot_per_month_user = anzahl_aktien_pro_monat - favs_pro_monat_eff
    rot_per_month_user = max(0, rot_per_month_user)

    if not rot_list:
        rot_per_month_user = 0

    rot_per_month_eff = rot_per_month_user
    info_adjustments = []

    # -----------------------------
    # ✅ Favoriten-Gewichtung via Multiplikator
    # -----------------------------
    if not fav_list:
        fav_multiplier = 0.0
    else:
        fav_multiplier = auto_fav_multiplier(anzahl_aktien_pro_monat) if auto_modus else float(fav_multiplier_manual)

    fav_count = favs_pro_monat_eff
    rot_count = rot_per_month_eff

    fav_rate_per_fav, rot_rate = compute_rates_with_multiplier(
        aktien_budget_month=aktien_budget,
        fav_count=fav_count,
        rot_count=rot_count,
        fav_multiplier=fav_multiplier
    )

    # -----------------------------
    # Mindestbetrag-Logik (Rotation) — nutzt rot_rate, reduziert rot_count und rechnet neu
    # -----------------------------
    if rot_per_month_eff > 0 and min_rate_rotation > 0:
        if rot_rate < min_rate_rotation:
            # maximale Rotation-Anzahl, so dass rot_rate >= min_rate_rotation
            # rot_rate = aktien_budget / (fav_count*fav_multiplier + rot_count)
            # => rot_count <= (aktien_budget/min_rate) - fav_count*fav_multiplier
            max_rot_count = int((aktien_budget / min_rate_rotation) - (fav_count * fav_multiplier))
            max_rot_count = max(0, max_rot_count)

            if max_rot_count < rot_per_month_eff:
                info_adjustments.append(
                    f"Rotation-Aktien/Monat von {rot_per_month_eff} auf {max_rot_count} reduziert "
                    f"(Mindestbetrag {min_rate_rotation:.2f}€)."
                )
                rot_per_month_eff = max_rot_count

                # neu rechnen
                rot_count = rot_per_month_eff
                fav_rate_per_fav, rot_rate = compute_rates_with_multiplier(
                    aktien_budget_month=aktien_budget,
                    fav_count=fav_count,
                    rot_count=rot_count,
                    fav_multiplier=fav_multiplier
                )

    # Wenn Rotation effektiv 0: alles in Favoriten (falls vorhanden)
    if rot_per_month_eff == 0 and fav_list:
        fav_rate_per_fav, rot_rate = compute_rates_with_multiplier(
            aktien_budget_month=aktien_budget,
            fav_count=fav_count,
            rot_count=0,
            fav_multiplier=fav_multiplier
        )
        info_adjustments.append("Keine Rotation möglich -> gesamtes Aktienbudget geht in Favoriten.")

    # -----------------------------
    # Rotation: Shuffle + optional Subset
    # -----------------------------
    slots_rot_total = monate * rot_per_month_eff
    rot_list_effective = rot_list[:]  # copy

    import random

    if shuffle_rotation and len(rot_list_effective) > 1:
        seed = safe_int(seed_text, default=420) if seed_text.strip() else None
        random.seed(seed)
        random.shuffle(rot_list_effective)

    if begrenze_rotation and rot_per_month_eff > 0 and len(rot_list_effective) > slots_rot_total:
        dropped = len(rot_list_effective) - slots_rot_total
        rot_list_effective = rot_list_effective[:slots_rot_total]
        info_adjustments.append(
            f"Rotation gekürzt: {len(rot_list)} eingegeben, aber nur {slots_rot_total} Rotation-Slots "
            f"({monate}×{rot_per_month_eff}) → {dropped} Werte wurden nicht berücksichtigt."
        )
    else:
        if rot_per_month_eff > 0 and len(rot_list_effective) > slots_rot_total and slots_rot_total > 0:
            info_adjustments.append(
                f"Hinweis: {len(rot_list_effective)} Rotation-Aktien eingegeben, aber nur {slots_rot_total} Slots verfügbar "
                f"({monate}×{rot_per_month_eff}). Nicht alle werden bespart."
            )

    # -----------------------------
    # Roadmaps
    # -----------------------------
    fav_roadmap, rot_roadmap = [], []

    for i in range(int(monate)):
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
            if len(rot) < rot_per_month_eff:
                rot += rot_list_effective[0:rot_per_month_eff - len(rot)]
            rot_roadmap.append(rot)
        else:
            rot_roadmap.append([])

    # Summen aggregieren
    aktien_sum = {}
    for monat in range(int(monate)):
        for aktie in fav_roadmap[monat]:
            aktien_sum[aktie] = aktien_sum.get(aktie, 0) + fav_rate_per_fav
        for aktie in rot_roadmap[monat]:
            aktien_sum[aktie] = aktien_sum.get(aktie, 0) + rot_rate

    etf_sum = {etf: etf_raten.get(etf, 0) * int(monate) for etf in etf_list}

    # -----------------------------
    # Infos
    # -----------------------------
    if info_limits:
        for msg in info_limits:
            st.info(msg)

    if fav_list:
        if auto_modus:
            st.info(f"Auto-Modus aktiv: Favoriten-Multiplikator = **{fav_multiplier:.1f}×**.")
        else:
            st.info(f"Manuell: Favoriten-Multiplikator = **{fav_multiplier:.1f}×**.")

        if rot_per_month_eff > 0:
            st.caption(f"Pro Monat: Favorit ≈ {fav_rate_per_fav:.2f}€ je Aktie | Rotation ≈ {rot_rate:.2f}€ je Aktie")

    if shuffle_rotation:
        if seed_text.strip():
            st.caption(
                f"Rotation wird gemischt (Seed: {safe_int(seed_text)}). "
                f"Gleiche Eingaben + gleicher Seed = gleiche Auswahl."
            )
        else:
            st.caption("Rotation wird gemischt (ohne Seed). Jede Berechnung kann anders ausfallen.")

    if info_adjustments:
        for msg in info_adjustments:
            st.info(msg)

    # -----------------------------
    # Export DataFrame
    # -----------------------------
    all_data = []
    for aktie, betrag in aktien_sum.items():
        typ = "Favorit" if aktie in fav_list else "Rotation"
        all_data.append({"Name": aktie, "Typ": typ, "Gesamtbetrag (€)": round(betrag, 2)})

    for etf, betrag in etf_sum.items():
        all_data.append({"Name": etf, "Typ": "ETF", "Gesamtbetrag (€)": round(betrag, 2)})

    df_export = pd.DataFrame(all_data)

    st.subheader("Gesamtübersicht")
    st.dataframe(df_export)

    csv = df_export.to_csv(index=False).encode("utf-8")
    st.download_button("CSV herunterladen", data=csv, file_name="sparplan_gesamtuebersicht.csv", mime="text/csv")

    # -----------------------------
    # Visualisierung: Verteilung nach Sparplan (Top-N, ohne Others-Balken)
    # -----------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    farben = {"Favorit": "tab:green", "Rotation": "tab:orange", "ETF": "tab:blue"}

    df_sorted = df_export.sort_values(by="Gesamtbetrag (€)", ascending=False)

    rest_sum = 0.0
    if len(df_sorted) > top_n_chart:
        df_plot = df_sorted.head(top_n_chart).copy()
        rest_sum = df_sorted.iloc[top_n_chart:]["Gesamtbetrag (€)"].sum()
    else:
        df_plot = df_sorted

    farben_liste = [farben.get(typ, "gray") for typ in df_plot["Typ"]]

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

    # -----------------------------
    # Visualisierung: Verteilung nach Typ
    # -----------------------------
    gruppe = df_export.groupby("Typ")["Gesamtbetrag (€)"].sum()
    farben_liste = [farben.get(typ, "gray") for typ in gruppe.index]
    fig1, ax1 = plt.subplots()
    ax1.bar(gruppe.index, gruppe.values, color=farben_liste)
    ax1.set_title("Verteilung nach Typ")
    ax1.set_ylabel("Gesamtbetrag (€)")
    st.pyplot(fig1)

    # -----------------------------
    # Visualisierung: ETF-Allokation
    # -----------------------------
    etf_df = df_export[df_export["Typ"] == "ETF"]
    if not etf_df.empty:
        fig2, ax2 = plt.subplots()
        ax2.pie(etf_df["Gesamtbetrag (€)"], labels=etf_df["Name"], autopct='%1.1f%%', startangle=140)
        ax2.set_title("ETF-Allokation")
        st.pyplot(fig2)

    st.success("Sparplan erfolgreich berechnet!")

    # -----------------------------
    # Depotwachstum simulieren (Zinseszins)
    # -----------------------------
    with st.expander("📈 Depotwachstum simulieren"):
        st.markdown("Vereinfachte Simulation mit konstanter Rendite (ohne Gebühren/Steuern).")

        fig, ax = plt.subplots()
        renditen = {
            "Underperform (4%)": 0.04,
            "Default (8%)": 0.08,
            "Overperform (20%)": 0.20,
            "Godmode (50%)": 0.50
        }

        monate_int = int(monate)
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

    # -----------------------------
    # Monatliche Raten: Monats-Auswahl + optional alle Monate
    # -----------------------------
    st.subheader("Monatliche Raten")

    show_all = st.checkbox("Alle Monate anzeigen (lang)", value=False)

    def render_month(m_index: int):
        st.markdown(f"**Monat {m_index + 1} – Aktien**")

        for aktie in fav_roadmap[m_index]:
            st.markdown(f"**{aktie}**: {fav_rate_per_fav:.2f} €")

        for aktie in rot_roadmap[m_index]:
            st.markdown(f"{aktie}: {rot_rate:.2f} €")

        st.markdown("**ETFs**")
        for etf in etf_list:
            st.markdown(f"**{etf}**: {etf_raten.get(etf, 0):.2f} €")

    if show_all:
        for m in range(monate_int):
            with st.expander(f"Monat {m + 1} anzeigen", expanded=False):
                render_month(m)
    else:
        month_choice = st.selectbox(
            "Monat auswählen",
            options=list(range(1, monate_int + 1)),
            index=0
        )
        with st.expander("Details anzeigen", expanded=True):
            render_month(month_choice - 1)