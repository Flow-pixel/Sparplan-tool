
import streamlit as st

st.title("Dynamischer Sparplan-Rechner")

# Eingabefelder
zielsumme = st.number_input("Zielsumme (€)", min_value=0, value=10000)
monate = st.number_input("Dauer (Monate)", min_value=1, value=20)

monatlicher_betrag = zielsumme / monate
st.markdown(f"**Monatlicher Sparbetrag: {monatlicher_betrag:.2f} €**")

aktienanteil = st.slider("Aktienanteil (%)", min_value=0, max_value=100, value=60)
etf_anteil = 100 - aktienanteil
st.markdown(f"**ETFs erhalten {etf_anteil} %, Aktien erhalten {aktienanteil} %**")

faktor = st.number_input("Faktor Favoriten vs Rotation (z. B. 2 bedeutet 2:1)", min_value=1, value=2)

# Eingabelisten
favoriten_input = st.text_area("Favoritenaktien (eine pro Zeile)", height=150)
rotation_input = st.text_area("Weitere Aktien (eine pro Zeile)", height=150)
etfs_input = st.text_area("ETFs (eine pro Zeile)", height=100)

# Liste parsen
favoriten = [f.strip() for f in favoriten_input.splitlines() if f.strip()]
rotation_aktien = [f.strip() for f in rotation_input.splitlines() if f.strip()]
etfs = [f.strip() for f in etfs_input.splitlines() if f.strip()]

# Sparplanberechnung
def berechne_sparplan(zielsumme, monate, aktienanteil, faktor, favoriten, rotation_aktien, etfs):
    gesamt_rate = zielsumme / monate
    aktien_rate = gesamt_rate * (aktienanteil / 100)
    etf_rate = gesamt_rate * (1 - aktienanteil / 100)

    # Aufteilung Aktienrate
    gesamt_faktor = faktor * len(favoriten) + len(rotation_aktien)
    if gesamt_faktor == 0:
        st.warning("Bitte mindestens eine Aktie eingeben.")
        return

    fav_rate = aktien_rate * (faktor * len(favoriten)) / gesamt_faktor
    rot_rate = aktien_rate * (len(rotation_aktien)) / gesamt_faktor

    fav_pro_aktie = fav_rate / len(favoriten) if favoriten else 0
    rot_pro_aktie = rot_rate / len(rotation_aktien) if rotation_aktien else 0
    etf_pro_etf = etf_rate / len(etfs) if etfs else 0

    # Ausgabe
    st.success("Sparplan erfolgreich berechnet!")
    st.write("### Monatliche Raten:")
    for f in favoriten:
        st.write(f"{f}: {fav_pro_aktie:.2f} €")
    for r in rotation_aktien:
        st.write(f"{r}: {rot_pro_aktie:.2f} €")
    for e in etfs:
        st.write(f"{e}: {etf_pro_etf:.2f} €")

# Button wieder einfügen
if st.button("Sparplan berechnen"):
    berechne_sparplan(
        zielsumme, monate, aktienanteil, faktor,
        favoriten, rotation_aktien, etfs
    )
