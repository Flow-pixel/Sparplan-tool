
import streamlit as st
import math

st.set_page_config(page_title="Dynamischer Sparplan-Rechner", layout="wide")

st.title("Dynamischer Sparplan-Rechner")

zielsumme = st.number_input("Zielsumme (€)", value=10000)
monate = st.number_input("Dauer (Monate)", value=20)
monatlicher_betrag = zielsumme / monate
st.markdown(f"### Monatlicher Sparbetrag: {monatlicher_betrag:.2f} €")

aktienanteil = st.slider("Aktienanteil (%)", 0, 100, 60)
etf_anteil = 100 - aktienanteil
st.markdown(f"**ETFs erhalten {etf_anteil} %, Aktien erhalten {aktienanteil} %**")

anzahl_aktien_pro_monat = st.number_input("Wie viele Aktien pro Monat besparen?", min_value=3, max_value=30, value=5)
st.caption("Davon sind automatisch 2 Favoriten enthalten, der Rest wird aus den weiteren Aktien rotierend ergänzt.")

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
    
# ETF-Verteilung: 50 % auf MSCI World & S&P 500, Rest gleichmäßig auf andere
msci_etfs = ["MSCI World", "S&P 500"]
priorisierte_etfs = [etf for etf in etf_list if etf in msci_etfs]
sonstige_etfs = [etf for etf in etf_list if etf not in msci_etfs]
etf_raten = {}
if etf_list:
    if priorisierte_etfs:
        priorisiertes_budget = etf_budget * 0.5
        rate_priorisiert = priorisiertes_budget / len(priorisierte_etfs)
        for etf in priorisierte_etfs:
            etf_raten[etf] = rate_priorisiert
    if sonstige_etfs:
        sonstiges_budget = etf_budget * 0.5
        rate_sonstig = sonstiges_budget / len(sonstige_etfs)
        for etf in sonstige_etfs:
            etf_raten[etf] = rate_sonstig

    rot_per_month = anzahl_aktien_pro_monat - 2

    # Favoriten rotieren: 2 pro Monat
    fav_roadmap = []
    for i in range(monate):
        start = (i * 2) % len(fav_list)
        favs = fav_list[start:start + 2]
        if len(favs) < 2:
            favs += fav_list[0:2 - len(favs)]
        fav_roadmap.append(favs)

    # Rotierende Aktien: restliche pro Monat
    rot_roadmap = []
    for i in range(monate):
        start = (i * rot_per_month) % len(rot_list)
        rot = rot_list[start:start + rot_per_month]
        if len(rot) < rot_per_month:
            rot += rot_list[0:rot_per_month - len(rot)]
        rot_roadmap.append(rot)

    aktien_budget = monatlicher_betrag * aktienanteil / 100
    etf_budget = monatlicher_betrag * etf_anteil / 100

    fav_rate = aktien_budget * 0.5 / 2
    rot_rate = aktien_budget * 0.5 / rot_per_month if rot_per_month else 0

    st.success("Sparplan erfolgreich berechnet!")
    st.subheader("Monatliche Raten:")

    for monat in range(monate):
        st.markdown(f"---\n**Monat {monat + 1} – Aktien**")
        for aktie in fav_roadmap[monat]:
            st.markdown(f"**{aktie}**: {fav_rate:.2f} €")
        for aktie in rot_roadmap[monat]:
            st.markdown(f"{aktie}: {rot_rate:.2f} €")
            st.markdown(f"**ETFs**")
for etf in etf_list:
    if etf in etf_raten:
        st.markdown(f"**{etf}**: {etf_raten[etf]:.2f} €")
    else:
        st.warning(f"Kein Eintrag für ETF '{etf}' gefunden.")
