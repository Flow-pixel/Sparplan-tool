import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dynamischer Sparplan-Rechner", layout="wide")

# Logo und Branding
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
    "Favoriten werden mit höherer Kapital-Gewichtung eingeplant. "
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
MSCI EM USD (Acc)
MSCI World Small Cap USD (Acc)
Physical Gold USD (Acc)
Space Innovators USD (Acc)
STOXX Global Dividend 100 EU"""

favoriten = st.text_area("Favoritenaktien (eine pro Zeile)", value=default_favoriten)
st.caption("Falls keine Favoriten angegeben sind, wird das gesamte Aktienbudget auf rotierende Aktien verteilt.")

rotation_aktien = st.text_area("Weitere Aktien (eine pro Zeile)", value=default_aktien)
etfs = st.text_area("ETFs (eine pro Zeile)", value=default_etfs)
st.caption("Falls keine ETFs angegeben sind, wird das gesamte Kapital auf Aktien verteilt.")

# -----------------------------
# Neue Optionen (deine Wünsche)
# -----------------------------
st.subheader("⚙️ Erweiterte Einstellungen")

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

# Favoriten pro Monat
favs_pro_monat = st.slider("Wie viele Favoriten pro Monat besparen?", 1, 3, 2)

# Auto-Modus für Gewichtung
auto_modus = st.checkbox(
    "Auto-Modus: Favoriten-Gewichtung automatisch anpassen (empfohlen für Anfänger)",
    value=True
)

min_rate_rotation = st.number_input(
    "Mindestbetrag pro Rotation-Aktie (€/Monat) – falls nötig wird die Anzahl Rotation-Aktien pro Monat automatisch reduziert",
    min_value=0.0,
    value=20.0,
    step=1.0
)

# Slider nur, wenn Auto-Modus aus
fav_share_manual = None
if not auto_modus:
    fav_share_manual = st.slider(
        "Favoriten-Anteil innerhalb Aktienbudget (%)",
        min_value=0,
        max_value=100,
        value=40
    )

# Diagramm-Limit
top_n_chart = st.slider("Diagramm: Anzahl angezeigter Positionen", 10, 120, 40)

# -----------------------------
# Helper: Auto-Gewichtung
# -----------------------------
def auto_fav_share(total_stocks_per_month: int) -> int:
    """
    Simple, anfängerfreundliche Heuristik:
    - Wenige Aktien/Monat -> Favorit stärker gewichten
    - Viele Aktien/Monat  -> Favorit weniger gewichten
    """
    share = 50 - 3 * total_stocks_per_month
    share = max(15, min(45, share))
    return int(share)

# -----------------------------
# Berechnung
# -----------------------------
if st.button("Sparplan berechnen"):

    fav_list = [f.strip() for f in favoriten.splitlines() if f.strip()]
    rot_list = [r.strip() for r in rotation_aktien.splitlines() if r.strip()]
    etf_list = [e.strip() for e in etfs.splitlines() if e.strip()]

    # Guard: Monate
    if not monate or monate <= 0:
        st.error("Die Dauer (Monate) muss größer als 0 sein.")
        st.stop()

    # Wenn keine ETFs, dann 100% Aktien
    if not etf_list:
        aktienanteil = 100
        etf_anteil = 0

    monatlicher_betrag = zielsumme / monate
    aktien_budget = monatlicher_betrag * aktienanteil / 100
    etf_budget = monatlicher_betrag * etf_anteil / 100

    # -----------------------------
    # ETF-Raten: feste Zielgewichte (wie besprochen)
    # Core MSCI World 25%
    # BlackRock World Mining 5%
    # Automation & Robotics 5%
    # MSCI World Small Cap 5%
    # Rest je 10% (normalisiert, falls ETFs fehlen/abweichen)
    # -----------------------------
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

    raw_weights = {etf: etf_weight_for(etf) for etf in etf_list}
    total_w = sum(raw_weights.values())

    etf_raten = {}
    if total_w > 0:
        for etf, w in raw_weights.items():
            etf_raten[etf] = etf_budget * (w / total_w)
    else:
        if len(etf_list) > 0:
            equal = etf_budget / len(etf_list)
            for etf in etf_list:
                etf_raten[etf] = equal

    # -----------------------------
    # Favoriten/Rotation: Anzahl pro Monat + Guards
    # -----------------------------
    favs_pro_monat_eff = min(favs_pro_monat, len(fav_list)) if len(fav_list) > 0 else 0

    rot_per_month_user = anzahl_aktien_pro_monat - favs_pro_monat_eff
    rot_per_month_user = max(0, rot_per_month_user)

    if len(rot_list) == 0:
        rot_per_month_user = 0

    # -----------------------------
    # Gewichtung Favorit/Rotation
    # -----------------------------
    if len(fav_list) == 0:
        fav_share = 0
    else:
        if auto_modus:
            fav_share = auto_fav_share(anzahl_aktien_pro_monat)
        else:
            fav_share = int(fav_share_manual)

    rot_share = 100 - fav_share

    fav_budget_month = aktien_budget * fav_share / 100
    rot_budget_month = aktien_budget * rot_share / 100

    # -----------------------------
    # Mindestbetrag-Logik (Option 1)
    # -----------------------------
    rot_per_month_eff = rot_per_month_user
    info_adjustments = []

    if rot_per_month_eff > 0 and min_rate_rotation > 0:
        rot_rate_candidate = rot_budget_month / rot_per_month_eff if rot_per_month_eff else 0
        if rot_rate_candidate < min_rate_rotation:
            max_rot_count = int(rot_budget_month // min_rate_rotation) if min_rate_rotation > 0 else rot_per_month_eff
            max_rot_count = max(0, max_rot_count)
            if max_rot_count < rot_per_month_eff:
                info_adjustments.append(
                    f"Rotation-Aktien/Monat von {rot_per_month_eff} auf {max_rot_count} reduziert "
                    f"(Mindestbetrag {min_rate_rotation:.2f}€)."
                )
                rot_per_month_eff = max_rot_count

    if rot_per_month_eff == 0 and len(fav_list) > 0:
        fav_budget_month = aktien_budget
        rot_budget_month = 0
        fav_share = 100
        rot_share = 0
        info_adjustments.append("Keine Rotation möglich -> gesamtes Aktienbudget geht in Favoriten.")

    # -----------------------------
    # Rotation: Shuffle (immer wenn aktiv) + optional Subset
    # -----------------------------
    slots_rot_total = monate * rot_per_month_eff
    rot_list_effective = rot_list[:]  # copy

    import random

    # 1) Shuffle
    if shuffle_rotation and len(rot_list_effective) > 1:
        seed_clean = seed_text.strip()
        if seed_clean:
            random.seed(int(seed_clean))  # reproduzierbar
        else:
            random.seed(None)  # echter Zufall
        random.shuffle(rot_list_effective)

    # 2) Subset (nur Kürzen)
    if begrenze_rotation and rot_per_month_eff > 0 and len(rot_list_effective) > slots_rot_total:
        dropped = len(rot_list_effective) - slots_rot_total
        rot_list_effective = rot_list_effective[:slots_rot_total]
        info_adjustments.append(
            f"Rotation gekürzt: {len(rot_list)} eingegeben, aber nur {slots_rot_total} Rotation-Slots "
            f"({monate}×{rot_per_month_eff}) → {dropped} Werte wurden nicht berücksichtigt."
        )
    else:
        if rot_per_month_eff > 0 and len(rot_list) > slots_rot_total and slots_rot_total > 0:
            info_adjustments.append(
                f"Hinweis: {len(rot_list)} Rotation-Aktien eingegeben, aber nur {slots_rot_total} Slots verfügbar "
                f"({monate}×{rot_per_month_eff}). Nicht alle werden bespart."
            )

    # Favoriten- und Rotations-Roadmap erstellen
    fav_roadmap, rot_roadmap = [], []

    for i in range(monate):
        # Favoriten für Monat i
        if favs_pro_monat_eff > 0:
            start_fav = i % len(fav_list)
            favs = []
            for k in range(favs_pro_monat_eff):
                favs.append(fav_list[(start_fav + k) % len(fav_list)])
        else:
            favs = []
        fav_roadmap.append(favs)

        # Rotation für Monat i
        if rot_per_month_eff > 0:
            start_rot = (i * rot_per_month_eff) % len(rot_list_effective)
            rot = rot_list_effective[start_rot:start_rot + rot_per_month_eff]
            if len(rot) < rot_per_month_eff:
                rot += rot_list_effective[0:rot_per_month_eff - len(rot)]
            rot_roadmap.append(rot)
        else:
            rot_roadmap.append([])

    # Monatsraten berechnen
    fav_rate_per_fav = (fav_budget_month / favs_pro_monat_eff) if favs_pro_monat_eff > 0 else 0
    rot_rate = (rot_budget_month / rot_per_month_eff) if rot_per_month_eff > 0 else 0

    # Summen aggregieren
    aktien_sum = {}
    for monat in range(monate):
        for aktie in fav_roadmap[monat]:
            aktien_sum[aktie] = aktien_sum.get(aktie, 0) + fav_rate_per_fav
        for aktie in rot_roadmap[monat]:
            aktien_sum[aktie] = aktien_sum.get(aktie, 0) + rot_rate

    etf_sum = {etf: etf_raten.get(etf, 0) * monate for etf in etf_list}

    # Info-Ausgaben (Transparenz)
    if auto_modus and len(fav_list) > 0:
        st.info(f"Auto-Modus aktiv: Favoriten-Anteil im Aktienbudget wurde auf **{fav_share}%** gesetzt.")
    if shuffle_rotation:
        if seed_text.strip():
            st.caption(f"Rotation wird gemischt (Seed: {seed_text.strip()}). Gleiche Eingaben + gleicher Seed = gleiche Auswahl.")
        else:
            st.caption("Rotation wird gemischt (ohne Seed). Jede Berechnung kann anders ausfallen.")

    if info_adjustments:
        for msg in info_adjustments:
            st.info(msg)

    # Export DataFrame
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
    # Depotwachstum-Simulation (vereinfacht)
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

        ax.set_title("Depotwachstum (vereinfacht)")
        ax.set_xlabel("Monat")
        ax.set_ylabel("Depotwert (€)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    # -----------------------------
    # Monatliche Raten
    # -----------------------------
    st.subheader("Monatliche Raten:")
    for monat in range(monate):
        st.markdown(f"---\n**Monat {monat + 1} – Aktien**")

        for aktie in fav_roadmap[monat]:
            st.markdown(f"**{aktie}**: {fav_rate_per_fav:.2f} €")

        for aktie in rot_roadmap[monat]:
            st.markdown(f"{aktie}: {rot_rate:.2f} €")

        st.markdown("**ETFs**")
        for etf in etf_list:
            st.markdown(f"**{etf}**: {etf_raten.get(etf, 0):.2f} €")