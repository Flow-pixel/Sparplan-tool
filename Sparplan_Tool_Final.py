
import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

st.set_page_config(page_title="Dynamischer Sparplan-Rechner", layout="wide")

# Logo auf der Hauptseite anzeigen
col1, col2 = st.columns([1, 4])  # Verhältnis: Logo zu Text
with col1:
    logo = Image.open("traderise_logo.png")
    st.image(logo, width=60)  # Größe bei Bedarf anpassen

with col2:
    st.markdown(
        '<div style="padding-top: 20px;">'
        'Powered by <a href="https://traderise.net" target="_blank">Traderise.net</a>'
        '</div>',
        unsafe_allow_html=True
    )

st.title("Dynamischer Sparplan-Rechner")

# Eingaben
zielsumme = st.number_input("Zielsumme (€)", value=10000)
monate = st.number_input("Dauer (Monate)", value=20)
aktienanteil = st.slider("Aktienanteil (%)", 0, 100, 60)
etf_anteil = 100 - aktienanteil
monatlicher_betrag = zielsumme / monate
aktien_budget = monatlicher_betrag * aktienanteil / 100
etf_budget = monatlicher_betrag * etf_anteil / 100

st.markdown(f"**ETFs erhalten {etf_anteil} %, Aktien erhalten {aktienanteil} %**")
st.markdown(f"### Monatlicher Sparbetrag: {monatlicher_betrag:.2f} €")

anzahl_aktien_pro_monat = st.number_input("Wie viele Aktien pro Monat besparen?", min_value=3, max_value=30, value=5)
st.caption("Darin ist automatisch 1 Favorit enthalten, der Rest wird aus den weiteren Aktien rotierend ergänzt. Favoriten werden mit einer höheren Kapital-Gewichtung eingeplant.")

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
st.caption("Falls keine Favoriten angegeben sind, wird das gesamte Aktienbudget auf rotierende Aktien verteilt.")
rotation_aktien = st.text_area("Weitere Aktien (eine pro Zeile)", value=default_aktien)
etfs = st.text_area("ETFs (eine pro Zeile)", value=default_etfs)
st.caption("Falls keine ETFs angegeben sind, wird das gesamte Kapital auf Aktien verteilt.")

if st.button("Sparplan berechnen"):
    fav_list = [f.strip() for f in favoriten.splitlines() if f.strip()]
    rot_list = [r.strip() for r in rotation_aktien.splitlines() if r.strip()]
    etf_list = [e.strip() for e in etfs.splitlines() if e.strip()]

    if not etf_list:
        aktienanteil = 100
        etf_anteil = 0

    aktien_budget = monatlicher_betrag * aktienanteil / 100
    etf_budget = monatlicher_betrag * etf_anteil / 100

    msci_etfs = ["MSCI World", "S&P 500"]
    priorisierte_etfs = [etf for etf in etf_list if etf in msci_etfs]
    sonstige_etfs = [etf for etf in etf_list if etf not in msci_etfs]
    etf_raten = {}

    if len(etf_list) == 1:
        etf_raten[etf_list[0]] = etf_budget
    else:
        if priorisierte_etfs:
            priorisiertes_budget = etf_budget * 0.5
            rate_priorisiert = priorisiertes_budget / len(priorisierte_etfs)
            for etf in priorisierte_etfs:
                etf_raten[etf] = rate_priorisiert
        if sonstige_etfs:
            sonstiges_budget = etf_budget * 0.5 if priorisierte_etfs else etf_budget
            rate_sonstig = sonstiges_budget / len(sonstige_etfs)
            for etf in sonstige_etfs:
                etf_raten[etf] = rate_sonstig

    rot_per_month = anzahl_aktien_pro_monat - 1 if len(fav_list) >= 1 else anzahl_aktien_pro_monat
    fav_roadmap, rot_roadmap = [], []

    for i in range(monate):
        if len(fav_list) >= 1:
            start_fav = i % len(fav_list)
            favs = [fav_list[start_fav]]
        else:
            favs = []
        fav_roadmap.append(favs)

        start_rot = (i * rot_per_month) % len(rot_list)
        rot = rot_list[start_rot:start_rot + rot_per_month]
        if len(rot) < rot_per_month:
            rot += rot_list[0:rot_per_month - len(rot)]
        rot_roadmap.append(rot)

    if len(fav_list) > 0:
        fav_rate = aktien_budget * 0.4
        rot_rate = aktien_budget * 0.6 / rot_per_month if rot_per_month else 0
    else:
        fav_rate = 0
        rot_rate = aktien_budget / rot_per_month if rot_per_month else 0

    aktien_sum = {}
    for monat in range(monate):
        for aktie in fav_roadmap[monat]:
            aktien_sum[aktie] = aktien_sum.get(aktie, 0) + fav_rate
        for aktie in rot_roadmap[monat]:
            aktien_sum[aktie] = aktien_sum.get(aktie, 0) + rot_rate
    etf_sum = {etf: etf_raten.get(etf, 0) * monate for etf in etf_list}

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

    # Visualisierung mit Matplotlib – Balkendiagramm nach Typ
    fig, ax = plt.subplots(figsize=(10, 6))
    farben = {"Favorit": "tab:blue", "Rotation": "tab:orange", "ETF": "tab:green"}
    farben_liste = [farben.get(typ, "gray") for typ in df_export["Typ"]]

    df_export_sorted = df_export.sort_values(by="Gesamtbetrag (€)", ascending=False)

    ax.barh(
        df_export_sorted["Name"],
        df_export_sorted["Gesamtbetrag (€)"],
        color=farben_liste
    )
    ax.set_xlabel("Gesamtbetrag (€)")
    ax.set_title("Verteilung nach Sparplan")
    ax.invert_yaxis()
    st.pyplot(fig)

    # Visualisierung: Verteilung nach Typ
    import matplotlib.pyplot as plt

    gruppe = df_export.groupby("Typ")["Gesamtbetrag (€)"].sum()

    fig1, ax1 = plt.subplots()
    ax1.bar(gruppe.index, gruppe.values)
    ax1.set_title("Verteilung nach Typ")
    ax1.set_ylabel("Gesamtbetrag (€)")
    st.pyplot(fig1)

    # Visualisierung: ETF-Allokation
    etf_df = df_export[df_export["Typ"] == "ETF"]
    if not etf_df.empty:
        fig2, ax2 = plt.subplots()
        ax2.pie(etf_df["Gesamtbetrag (€)"], labels=etf_df["Name"], autopct='%1.1f%%', startangle=140)
        ax2.set_title("ETF-Allokation")
        st.pyplot(fig2)

    st.success("Sparplan erfolgreich berechnet!")
    st.subheader("Monatliche Raten:")
    for monat in range(monate):
        st.markdown(f"---\n**Monat {monat + 1} – Aktien**")
        for aktie in fav_roadmap[monat]:
            st.markdown(f"**{aktie}**: {fav_rate:.2f} €")
        for aktie in rot_roadmap[monat]:
            st.markdown(f"{aktie}: {rot_rate:.2f} €")
        st.markdown("**ETFs**")
        for etf in etf_list:
            st.markdown(f"**{etf}**: {etf_raten.get(etf, 0):.2f} €")
