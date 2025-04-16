
import streamlit as st
import pandas as pd

st.title("Sparplan-Rotationsrechner")

# Eingaben
zielsumme = st.number_input("Zielkapital (€)", value=12400)
monate = st.number_input("Anlagedauer (Monate)", value=20)
aktien_anteil = st.slider("Aktienanteil (%)", 0, 100, 60)
etf_anteil = 100 - aktien_anteil

favoriten_rate = st.number_input("Sparrate pro Favorit (€/Monat)", value=100)
favoriten_monate = st.number_input("Besparungsdauer je Favorit (Monate)", value=4)

rotation_rate = st.number_input("Sparrate pro rotierende Aktie (€/Monat)", value=50)
rotation_monate = st.number_input("Besparungsdauer je Rotation (Monate)", value=4)

favoriten = st.text_area("Favoritenaktien (eine pro Zeile)", value="Palantir Technologies\nCoinbase\nAlphabet\nCrowdStrike\nMercadoLibre\nASML\nVertiv").split("\n")
rotation_aktien = st.text_area("Weitere Aktien (eine pro Zeile)", value="NVIDIA\nRheinmetall\nTesla\nAdyen\nCRISPR Therapeutics\nBlock\nMicroStrategy\nProcter & Gamble\nAmazon\nApple\nMeta\nMicrosoft\nDatadog\nServiceNow\nUiPath\nEnphase\nPlug Power\nSea Limited\nAlnylam\nEli Lilly\nJohnson & Johnson\nLVMH").split("\n")

etfs = {
    "MSCI World": 0.25,
    "S&P 500": 0.20,
    "Emerging Markets": 0.15,
    "Physical Gold": 0.10,
    "Cybersecurity/AI (Thematisch)": 0.15,
    "EuroStoxx 600": 0.15
}

# Berechnung
def generate_sparplan():
    etf_gesamt = zielsumme * (etf_anteil / 100)
    etf_plan = []
    for name, gewicht in etfs.items():
        betrag = gewicht * etf_gesamt
        monatlich = betrag / monate
        etf_plan.append({
            "Monat": "1–" + str(monate),
            "Wertpapier": name,
            "Kategorie": "ETF",
            "Monatliche Rate (€)": round(monatlich, 2),
            "Besparungsdauer (Monate)": monate,
            "Gesamtbetrag (€)": round(betrag, 2)
        })

    favoriten_rotations = [favoriten[i:i+2] for i in range(0, len(favoriten), 2)]
    favoriten_sparplan = []
    monat_counter = 1
    for gruppe in favoriten_rotations:
        for m in range(monat_counter, monat_counter + favoriten_monate):
            for aktie in gruppe:
                favoriten_sparplan.append({
                    "Monat": m,
                    "Wertpapier": aktie,
                    "Kategorie": "Aktie (Favorit)",
                    "Monatliche Rate (€)": favoriten_rate,
                    "Besparungsdauer (Monate)": favoriten_monate,
                    "Gesamtbetrag (€)": favoriten_rate * favoriten_monate
                })
        monat_counter += favoriten_monate

    rotations = [rotation_aktien[i:i+6] for i in range(0, len(rotation_aktien), 6)]
    rotations_sparplan = []
    monat_counter = 1
    for gruppe in rotations:
        for m in range(monat_counter, monat_counter + rotation_monate):
            for aktie in gruppe:
                rotations_sparplan.append({
                    "Monat": m,
                    "Wertpapier": aktie,
                    "Kategorie": "Aktie (Rotation)",
                    "Monatliche Rate (€)": rotation_rate,
                    "Besparungsdauer (Monate)": rotation_monate,
                    "Gesamtbetrag (€)": rotation_rate * rotation_monate
                })
        monat_counter += rotation_monate

    return pd.DataFrame(favoriten_sparplan + rotations_sparplan + etf_plan)

if st.button("Sparplan berechnen"):
    plan = generate_sparplan()
    st.success("Sparplan erfolgreich erstellt!")
    st.dataframe(plan)
    csv = plan.to_csv(index=False).encode('utf-8')
    st.download_button("Ergebnisse als CSV herunterladen", csv, "sparplan.csv", "text/csv")
