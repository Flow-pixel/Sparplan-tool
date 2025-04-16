import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sparplan Tool", layout="wide")
st.title("Sparplan-Rotationsrechner (V1)")

# Eingaben
zielsumme = st.number_input("Zielkapital (€)", value=12400)
monate = st.number_input("Anlagedauer (Monate)", value=20, min_value=1)
monatlicher_betrag = zielsumme / monate
st.info(f"🔁 Monatlicher Sparbetrag ergibt sich zu: **{round(monatlicher_betrag, 2)} €**")

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

def calculate_total_sparbedarf():
    etf_summe = zielsumme * (etf_anteil / 100)
    etf_raten = sum([(etf_summe * gewicht) / monate for gewicht in etfs.values()])
    favoriten_summe = len(favoriten) * favoriten_monate * favoriten_rate
    rotation_summe = len(rotation_aktien) * rotation_monate * rotation_rate
    gesamt_summe = (favoriten_summe + rotation_summe) / monate + etf_raten
    return round(gesamt_summe, 2)

# Warnung und Auto-Korrektur
gesamt_rate = calculate_total_sparbedarf()
warnung_aktiv = gesamt_rate > monatlicher_betrag * 1.05

if warnung_aktiv:
    st.warning(f"⚠️ Deine geplanten Raten ergeben aktuell **{gesamt_rate} € / Monat**, was dein Ziel von {zielsumme} € in {monate} Monaten überschreiten würde.")

    if st.button("Auto-Korrektur starten"):
        gesamt_monatlich = zielsumme / monate
        etf_fix = sum([(zielsumme * (etf_anteil / 100) * gewicht) / monate for gewicht in etfs.values()])
        übriges_budget = gesamt_monatlich - etf_fix

        # Neue Raten gleichmäßig berechnen
        favoriten_rate = round(übriges_budget * 0.6 / (len(favoriten) * favoriten_monate), 2)
        rotation_rate = round(übriges_budget * 0.4 / (len(rotation_aktien) * rotation_monate), 2)
        st.success(f"Neue Sparraten gesetzt: Favoriten = {favoriten_rate} €, Rotation = {rotation_rate} €")

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
    st.success("✅ Sparplan erfolgreich erstellt!")
    st.dataframe(plan)
    csv = plan.to_csv(index=False).encode('utf-8')
    st.download_button("Ergebnisse als CSV herunterladen", csv, "sparplan.csv", "text/csv")


# Neue Auto-Korrektur-Logik
if 'auto_korrektur' not in st.session_state:
    st.session_state.auto_korrektur = False

if favoriten and favoriten_rate and rotation_rate:
    anzahl_favs = len(favoriten)
anzahl_rots = len(rotation_aktien)
    gesamt_rate = (favoriten_rate * anzahl_favs * favoriten_monate + 
                   rotation_rate * anzahl_rots * rotation_monate) / monate

    if gesamt_rate > monatlicher_betrag:
        st.warning(f"⚠️ Deine geplanten Raten ergeben aktuell {round(gesamt_rate, 2)} € / Monat, "
                   f"was dein Ziel von {zielsumme} € in {monate} Monaten überschreiten würde.")
        if st.button("Auto-Korrektur starten"):
            gesamt_faktor = (2 * anzahl_favs * favoriten_monate) + (1 * anzahl_rots * rotation_monate)
            if gesamt_faktor > 0:
                basisrate = zielsumme / monate / gesamt_faktor
                neue_fav_rate = round(basisrate * 2, 2)
                neue_rot_rate = round(basisrate, 2)
                st.success(f"✅ Neue Sparraten gesetzt: Favoriten = {neue_fav_rate} €, Rotation = {neue_rot_rate} €")
                favoriten_rate = neue_fav_rate
                rotation_rate = neue_rot_rate
                st.session_state.auto_korrektur = True

# Anzeige der aktualisierten Eingaben
if st.session_state.auto_korrektur:
    st.number_input("Sparrate pro Favorit (€/Monat)", value=favoriten_rate, key='updated_fav_rate')
    st.number_input("Sparrate pro rotierende Aktie (€/Monat)", value=rotation_rate, key='updated_rot_rate')
