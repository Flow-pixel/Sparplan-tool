
import streamlit as st
import pandas as pd

st.title("Dynamischer Sparplan-Rechner")

zielsumme = st.number_input("Zielsumme (€)", min_value=1000, value=10000, step=500)
monate = st.number_input("Dauer (Monate)", min_value=1, value=20, step=1)
aktienanteil = st.slider("Aktienanteil (%)", min_value=0, max_value=100, value=60)

monatlicher_betrag = zielsumme / monate
st.markdown(f"### Monatlicher Sparbetrag: {monatlicher_betrag:.2f} €")
st.markdown(f"**ETFs erhalten {100 - aktienanteil} %, Aktien erhalten {aktienanteil} %**")

faktor = st.number_input("Faktor Favoriten vs Rotation (z. B. 2 bedeutet 2:1)", min_value=1.0, value=2.0, step=0.5)

favoriten_input = st.text_area("Favoritenaktien (eine pro Zeile)", height=150)
rotation_input = st.text_area("Weitere Aktien (eine pro Zeile)", height=150)
etf_input = st.text_area("ETFs (eine pro Zeile)", height=120)

favoriten = [f.strip() for f in favoriten_input.splitlines() if f.strip()]
rotation_aktien = [r.strip() for r in rotation_input.splitlines() if r.strip()]
etfs = [e.strip() for e in etf_input.splitlines() if e.strip()]

# Wenn alles ausgefüllt ist
if favoriten and rotation_aktien and etfs:
    # Verteilung berechnen
    etf_budget = monatlicher_betrag * (1 - aktienanteil / 100)
    aktien_budget = monatlicher_betrag * (aktienanteil / 100)

    faktor_summe = faktor + 1
    fav_budget = aktien_budget * (faktor / faktor_summe)
    rota_budget = aktien_budget * (1 / faktor_summe)

    etf_rate = etf_budget / len(etfs)
    favoriten_rate = fav_budget / len(favoriten)
    rotation_rate = rota_budget / len(rotation_aktien)

    sparplan = []

    for monat in range(1, monate + 1):
        for etf in etfs:
            sparplan.append((monat, etf, "ETF", etf_rate))

        fav_index = (monat - 1) % len(favoriten)
        sparplan.append((monat, favoriten[fav_index], "Aktie (Favorit)", favoriten_rate))

        rot_index = (monat - 1) % len(rotation_aktien)
        sparplan.append((monat, rotation_aktien[rot_index], "Aktie (Rotation)", rotation_rate))

    df = pd.DataFrame(sparplan, columns=["Monat", "Wertpapier", "Kategorie", "Monatliche Rate (€)"])
    st.success("Sparplan erfolgreich berechnet!")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Ergebnisse als CSV herunterladen", csv, "sparplan.csv", "text/csv")
