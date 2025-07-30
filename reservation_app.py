import streamlit as st
import pyodbc
from datetime import datetime

# Connexion SQL Server
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=base_flot_kia;"
        "Trusted_Connection=yes;"
    )

# Récupérer la dernière réservation EN COURS
def get_last_reservation_en_cours():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 * FROM Reservations WHERE statut = 'en cours' ORDER BY date_creation DESC")
    row = cursor.fetchone()
    conn.close()
    return row

# Dernier kilométrage
def get_last_kilometrage_fin():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 kilometrage_fin FROM Reservations ORDER BY date_creation DESC")
    row = cursor.fetchone()
    conn.close()
    return row.kilometrage_fin if row else 0

# Conflit
def is_overlapping(date_debut, date_fin, heure_debut, heure_fin):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM Reservations
        WHERE date_debut = ?
          AND statut = 'en cours'
          AND (
                (heure_debut < ? AND heure_fin > ?) OR
                (heure_debut < ? AND heure_fin > ?) OR
                (heure_debut >= ? AND heure_fin <= ?)
              )
    """, date_debut, heure_fin, heure_debut, heure_debut, heure_fin, heure_debut, heure_fin)
    result = cursor.fetchall()
    conn.close()
    return len(result) > 0

# UI
st.set_page_config(page_title="Gestion de flotte", layout="centered")
st.title("🚗 Application de gestion des réservations de véhicules")

# Menu
mode = st.sidebar.radio("Menu", ["📥 Prendre une réservation", "✅ Terminer une réservation"])

# 📥 PRISE DE RÉSERVATION
if mode == "📥 Prendre une réservation":
    st.subheader("📥 Nouvelle réservation")

    km_debut = get_last_kilometrage_fin()
    st.session_state.setdefault("nom", "")
    st.session_state.setdefault("prenom", "")
    st.session_state.setdefault("motif", "")
    st.session_state.setdefault("km_fin", km_debut + 1)
    st.session_state.setdefault("date_debut", datetime.today().date())
    st.session_state.setdefault("date_fin", datetime.today().date())
    st.session_state.setdefault("heure_debut", datetime.now().time())
    st.session_state.setdefault("heure_fin", datetime.now().time())

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.nom = st.text_input("Nom", value=st.session_state.nom)
    with col2:
        st.session_state.prenom = st.text_input("Prénom", value=st.session_state.prenom)

    col3, col4 = st.columns(2)
    with col3:
        st.session_state.date_debut = st.date_input("📅 Date début", value=st.session_state.date_debut)
    with col4:
        st.session_state.date_fin = st.date_input("📅 Date fin", value=st.session_state.date_fin)

    col5, col6 = st.columns(2)
    with col5:
        st.session_state.heure_debut = st.time_input("🕒 Heure début", value=st.session_state.heure_debut)
    with col6:
        st.session_state.heure_fin = st.time_input("🕓 Heure fin", value=st.session_state.heure_fin)

    st.session_state.motif = st.text_input("📝 Motif", value=st.session_state.motif)

    col7, col8 = st.columns(2)
    with col7:
        st.number_input("📍 Kilométrage début", value=km_debut, disabled=True)
    with col8:
        st.session_state.km_fin = st.number_input("🏁 Kilométrage fin", min_value=km_debut + 1, value=st.session_state.km_fin)

    bcol1, bcol2 = st.columns(2)
    with bcol1:
        if st.button("✅ Valider la réservation"):
            if not st.session_state.nom or not st.session_state.prenom:
                st.error("❗ Veuillez renseigner le nom et le prénom.")
            elif is_overlapping(
                st.session_state.date_debut,
                st.session_state.date_fin,
                st.session_state.heure_debut,
                st.session_state.heure_fin
            ):
                st.error("❌ Une réservation existe déjà sur cette plage horaire.")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO Reservations (
                            nom, prenom, date_debut, date_fin,
                            heure_debut, heure_fin, motif,
                            kilometrage_debut, kilometrage_fin, statut
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, st.session_state.nom, st.session_state.prenom,
                         st.session_state.date_debut, st.session_state.date_fin,
                         st.session_state.heure_debut, st.session_state.heure_fin,
                         st.session_state.motif, km_debut, st.session_state.km_fin,
                         "en cours")
                    conn.commit()
                    conn.close()
                    st.success("✅ Réservation enregistrée avec succès !")
                    st.balloons()
                    st.session_state.nom = ""
                    st.session_state.prenom = ""
                    st.session_state.motif = ""
                    st.session_state.km_fin += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement : {e}")
    with bcol2:
        if st.button("❌ Annuler"):
            st.session_state.nom = ""
            st.session_state.prenom = ""
            st.session_state.motif = ""
            st.session_state.km_fin = get_last_kilometrage_fin() + 1
            st.warning("⛔ Réservation annulée.")
            st.rerun()

# ✅ TERMINER LA RÉSERVATION
elif mode == "✅ Terminer une réservation":
    st.subheader("✅ Terminer la dernière réservation en cours")

    last = get_last_reservation_en_cours()
    if not last:
        st.info("ℹ️ Aucune réservation en cours à terminer.")
    else:
        st.write(f"**ID réservation :** {last.id}")
        st.text_input("Nom", value=last.nom, disabled=True)
        st.text_input("Prénom", value=last.prenom, disabled=True)
        st.date_input("Date début", value=last.date_debut, disabled=True)
        st.time_input("Heure début", value=last.heure_debut, disabled=True)
        st.text_input("Motif", value=last.motif, disabled=True)
        st.number_input("Kilométrage début", value=last.kilometrage_debut, disabled=True)

        km_fin_new = st.number_input("🏁 Nouveau kilométrage fin", min_value=last.kilometrage_debut + 1)

        if st.button("🟢 Terminer la réservation"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Reservations
                    SET kilometrage_fin = ?, statut = ?
                    WHERE id = ?
                """, km_fin_new, "terminée", last.id)
                conn.commit()
                conn.close()
                st.success(f"✅ Réservation #{last.id} terminée avec succès !")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la mise à jour : {e}")
