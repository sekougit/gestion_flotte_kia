import streamlit as st
import pandas as pd
from datetime import datetime, date, time
import os

# Nom du fichier Excel
FICHIER = "reservations.xlsx"

# Initialiser le fichier si inexistant
if not os.path.exists(FICHIER):
    df_init = pd.DataFrame(columns=[
        'id', 'nom', 'prenom', 'date_debut', 'date_fin',
        'heure_debut', 'heure_fin', 'motif',
        'kilometrage_debut', 'kilometrage_fin',
        'statut', 'date_creation'
    ])
    df_init.to_excel(FICHIER, index=False)

# Charger les données
df = pd.read_excel(FICHIER)

# Fonctions
def get_last_kilometrage():
    if df.empty:
        return 0
    else:
        # On prend la dernière réservation terminée
        return df.loc[df['statut'] == 'terminée', 'kilometrage_fin'].max(skipna=True) or 0

def get_last_reservation_en_cours():
    en_cours = df[df['statut'] == 'en cours']
    if en_cours.empty:
        return None
    return en_cours.sort_values(by="date_creation", ascending=False).iloc[0]

def is_overlapping(date_debut, date_fin, heure_debut, heure_fin):
    for _, row in df[df['statut'] == 'en cours'].iterrows():
        if pd.to_datetime(row['date_debut']).date() == date_debut:
            h1 = pd.to_datetime(row['heure_debut']).time()
            h2 = pd.to_datetime(row['heure_fin']).time()
            if (
                (h1 < heure_fin and h2 > heure_debut) or
                (h1 < heure_debut and h2 > heure_fin) or
                (h1 >= heure_debut and h2 <= heure_fin)
            ):
                return True
    return False

# Interface Streamlit
st.set_page_config(page_title="Gestion de flotte Excel", layout="centered")
st.title("🚗 Application de gestion des réservations (Excel)")

mode = st.sidebar.radio("Menu", ["📥 Prendre une réservation", "✅ Terminer une réservation"])

# 📥 PRISE DE RÉSERVATION
if mode == "📥 Prendre une réservation":
    st.subheader("📥 Nouvelle réservation")

    km_debut = get_last_kilometrage()

    nom = st.text_input("Nom")
    prenom = st.text_input("Prénom")

    date_debut = st.date_input("📅 Date début", value=date.today())
    date_fin = st.date_input("📅 Date fin", value=date.today())
    heure_debut = st.time_input("🕒 Heure début", value=datetime.now().time())
    heure_fin = st.time_input("🕓 Heure fin", value=(datetime.now().replace(minute=30)).time())

    motif = st.text_input("📝 Motif")
    st.number_input("📍 Kilométrage début", value=km_debut, disabled=True)
    km_fin = st.number_input("🏁 Kilométrage fin", min_value=km_debut + 1)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Valider la réservation"):
            if not nom or not prenom:
                st.error("❗ Veuillez renseigner le nom et le prénom.")
            elif date_fin < date_debut:
                st.error("❗ La date de fin ne peut pas être avant la date de début.")
            elif date_debut == date_fin and heure_fin <= heure_debut:
                st.error("❗ L'heure de fin doit être après l'heure de début.")
            elif is_overlapping(date_debut, date_fin, heure_debut, heure_fin):
                st.error("❌ Ce créneau est déjà réservé.")
            else:
                new_id = int(df['id'].max() + 1) if not df.empty else 1
                new_row = {
                    'id': new_id,
                    'nom': nom,
                    'prenom': prenom,
                    'date_debut': date_debut,
                    'date_fin': date_fin,
                    'heure_debut': heure_debut,
                    'heure_fin': heure_fin,
                    'motif': motif,
                    'kilometrage_debut': km_debut,
                    'kilometrage_fin': km_fin,
                    'statut': 'en cours',
                    'date_creation': datetime.now()
                }
                df.loc[len(df)] = new_row
                df.to_excel(FICHIER, index=False)
                st.success("✅ Réservation enregistrée avec succès !")
                st.balloons()
                st.rerun()

    with col2:
        if st.button("❌ Annuler"):
            st.warning("⛔ Réservation annulée.")
            st.rerun()

# ✅ TERMINER LA RÉSERVATION
elif mode == "✅ Terminer une réservation":
    st.subheader("✅ Terminer la dernière réservation en cours")
    last = get_last_reservation_en_cours()

    if not last is None:
        st.write(f"**ID réservation :** {last['id']}")
        st.text_input("Nom", value=last['nom'], disabled=True)
        st.text_input("Prénom", value=last['prenom'], disabled=True)
        st.date_input("Date début", value=pd.to_datetime(last['date_debut']), disabled=True)
        st.time_input("Heure début", value=pd.to_datetime(str(last['heure_debut'])).time(), disabled=True)
        st.text_input("Motif", value=last['motif'], disabled=True)
        st.number_input("Kilométrage début", value=last['kilometrage_debut'], disabled=True)

        km_fin_new = st.number_input("🏁 Nouveau kilométrage fin", min_value=last['kilometrage_debut'] + 1)

        if st.button("🟢 Terminer la réservation"):
            idx = df[df['id'] == last['id']].index[0]
            df.at[idx, 'kilometrage_fin'] = km_fin_new
            df.at[idx, 'statut'] = 'terminée'
            df.to_excel(FICHIER, index=False)
            st.success("✅ Réservation terminée avec succès.")
            st.balloons()
            st.rerun()
    else:
        st.info("ℹ️ Aucune réservation en cours à terminer.")
