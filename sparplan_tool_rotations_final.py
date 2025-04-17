
import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="Dynamischer Sparplan-Rechner", layout="wide")

st.title("Dynamischer Sparplan-Rechner")

# Eingabefelder
zielsumme = st.number_input("Zielsumme (€)", value=10000)
monate = st.number_input("Dauer (Monate)", value=20)
monatlicher_betrag = zielsumme / monate
st.markdown(f"### Monatlicher Sparbetrag: {monatlicher_betrag:.2f} €")

aktienanteil = st.slider("Aktienanteil (%)", 0, 100, 60)
etf_anteil = 100 - aktienanteil
st.markdown(f"**ETFs erhalten {etf_anteil} %, Aktien erhalten {aktienanteil} %**")

faktor_favoriten = st.number_input("Faktor Favoriten vs Rotation (z. B. 2 bedeutet 2:1)", value=2)
anzahl_aktien_pro_monat = st.number_input("Wie viele Aktien pro Monat besparen?", min_value=1, max_value=30)
st.caption("Davon sind automatisch 2 Favoriten enthalten, der Rest wird aus den weiteren Aktien rotierend ergänzt.")"Wie viele Aktien pro Monat besparen?", value=5)

# Beispielwerte für die Platzhalter
default_favoriten = """Palantir Technologies
Coinbase
Alphabet
CrowdStrike
ASML
Vertiv
MercadoLibre"""

default_aktien = """NVIDIA
Rheinmetall
Tesla
Adyen
CRISPR Therapeutics
Block
MicroStrategy
Procter & Gamble
Amazon
Apple
Meta
Microsoft
Datadog
ServiceNow
UiPath
Enphase
Plug Power
Sea Limited
Alnylam
Eli Lilly
Johnson & Johnson
LVMH
Snowflake"""

default_etfs = """MSCI World
S&P 500
Emerging Markets
Physical Gold
Cybersecurity/AI (Thematisch)
EuroStoxx 600"""

favoriten = st.text_area("Favoritenaktien (eine pro Zeile)", value=default_favoriten)
rotation_aktien = st.text_area("Weitere Aktien (eine pro Zeile)", value=default_aktien)
etfs = st.text_area("ETFs (eine pro Zeile)", value=default_etfs)

if st.button("Sparplan berechnen"):
    fav_list = [f.strip() for f in favoriten.splitlines() if f.strip()]
    rot_list = [r.strip() for r in rotation_aktien.splitlines() if r.strip()]
    etf_list = [e.strip() for e in etfs.splitlines() if e.strip()]

    aktien_budget = monatlicher_betrag * aktienanteil / 100
    etf_budget = monatlicher_betrag * etf_anteil / 100

    ges_aktien = len(fav_list) * faktor_favoriten + len(rot_list)
    if ges_aktien == 0:
        ges_aktien = 1  # Vermeide Division durch 0

    fav_rate = aktien_budget / (len(fav_list) * faktor_favoriten + len(rot_list)) * faktor_favoriten
    rot_rate = aktien_budget / (len(fav_list) * faktor_favoriten + len(rot_list))

    etf_rate = etf_budget / len(etf_list) if etf_list else 0

    # Rotation auf Monate verteilen
    rot_monate = math.ceil(len(rot_list) / anzahl_aktien_pro_monat)
    rot_roadmap = []
    for i in range(monate):
        start = (i % rot_monate) * anzahl_aktien_pro_monat
        selected = rot_list[start:start + anzahl_aktien_pro_monat]
        rot_roadmap.append(selected)

    # Ausgabe
    st.success("Sparplan erfolgreich berechnet!")
    st.subheader("Monatliche Raten:")

    for aktie in fav_list:
        st.markdown(f"**{aktie}**: {fav_rate:.2f} €")

    for monat in range(monate):
        st.markdown(f"---
**Monat {monat + 1} – Rotierende Aktien**")
        for aktie in rot_roadmap[monat]:
            st.markdown(f"{aktie}: {rot_rate:.2f} €")

    for etf in etf_list:
        st.markdown(f"**{etf}**: {etf_rate:.2f} €")
