
import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Sparplan Tool", layout="wide")

st.title("Dynamischer Sparplan-Rechner")

zielsumme = st.number_input("Zielsumme (€)", min_value=1000, value=10000, step=500)
monate = st.number_input("Dauer (Monate)", min_value=1, value=20, step=1)

monatlicher_betrag = zielsumme / monate
st.markdown(f"**Monatlicher Sparbetrag: {monatlicher_betrag:.2f} €**")

aktien_anteil = st.slider("Aktienanteil (%)", 0, 100, 60)
etf_anteil = 100 - aktien_anteil

st.markdown(f"**ETFs erhalten {etf_anteil} %**, Aktien erhalten {aktien_anteil} %")

aktien_faktor_fav = st.number_input("Faktor Favoriten vs Rotation (z. B. 2 bedeutet 2:1)", min_value=1, value=2)

st.subheader("Wertpapierlisten")

favoriten_input = st.text_area("Favoritenaktien (eine pro Zeile)", height=150)
rotation_input = st.text_area("Weitere Aktien (Rotation, eine pro Zeile)", height=150)
etf_input = st.text_area("ETFs (eine pro Zeile)", height=100)

favoriten = [f.strip() for f in favoriten_input.strip().split("\n") if f.strip()]
rotation = [r.strip() for r in rotation_input.strip().split("\n") if r.strip()]
etfs = [e.strip() for e in etf_input.strip().split("\n") if e.strip()]

if st.button("Sparplan berechnen"):

    if not favoriten and not rotation and not etfs:
        st.error("Bitte gib mindestens eine Aktie oder einen ETF ein.")
    else:
        gesamt_aktien_betrag = monatlicher_betrag * aktien_anteil / 100
        gesamt_etf_betrag = monatlicher_betrag * etf_anteil / 100

        fav_gewicht = aktien_faktor_fav
        rot_gewicht = 1

        gesamt_gewicht = fav_gewicht * len(favoriten) + rot_gewicht * len(rotation)

        if gesamt_gewicht == 0:
            aktien_rates = {}
        else:
            einheit = gesamt_aktien_betrag / gesamt_gewicht

            aktien_rates = {}
            for f in favoriten:
                aktien_rates[f] = round(einheit * fav_gewicht, 2)
            for r in rotation:
                aktien_rates[r] = round(einheit * rot_gewicht, 2)

        etf_rate = round(gesamt_etf_betrag / len(etfs), 2) if etfs else 0

        data = []

        for monat in range(1, monate + 1):
            for etf in etfs:
                data.append({
                    "Monat": monat,
                    "Wertpapier": etf,
                    "Kategorie": "ETF",
                    "Monatliche Rate (€)": etf_rate
                })

            index_fav = (monat - 1) % len(favoriten) if favoriten else -1
            if index_fav != -1:
                fav_name = favoriten[index_fav]
                data.append({
                    "Monat": monat,
                    "Wertpapier": fav_name,
                    "Kategorie": "Favorit",
                    "Monatliche Rate (€)": aktien_rates.get(fav_name, 0)
                })

            rotation_group_size = math.ceil(monate / max(len(rotation), 1)) if rotation else 0
            rotation_index = ((monat - 1) // rotation_group_size) % len(rotation) if rotation_group_size > 0 else -1
            if rotation_index != -1:
                rot_name = rotation[rotation_index]
                data.append({
                    "Monat": monat,
                    "Wertpapier": rot_name,
                    "Kategorie": "Rotation",
                    "Monatliche Rate (€)": aktien_rates.get(rot_name, 0)
                })

        df = pd.DataFrame(data)

        st.success("Sparplan erfolgreich berechnet!")
        st.dataframe(df)
        st.download_button("Ergebnisse als CSV herunterladen", df.to_csv(index=False), "sparplan.csv", "text/csv")
