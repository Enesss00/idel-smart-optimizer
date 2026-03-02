import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from folium.features import DivIcon

# --- CONFIGURATION ---
st.set_page_config(page_title="IDEL Smart Optimizer", layout="wide", page_icon="🩺")

# Initialisation du Session State pour la persistance des données
if 'resultat_ia' not in st.session_state:
    st.session_state.resultat_ia = None

st.title("🩺 IDEL Smart Optimizer v1.1")
st.markdown("---")

# --- SIDEBAR : CONFIGURATION & DÉPLOIEMENT ---
with st.sidebar:
    st.header("🔑 Accès Premium")
    api_key = st.text_input("Clé API Business", type="password")

    st.header("⚙️ Paramètres")
    depot = st.text_input("Adresse du Cabinet", "1 rue de Rivoli, Paris")

    # URL de l'API (Prêt pour le Cloud)
    st.markdown("---")
    st.header("🌐 Connexion Serveur")
    api_url = st.text_input("URL de l'IA Engine", "http://127.0.0.1:8000", help="Laisse localhost pour le test local")

    if st.button("🗑️ Réinitialiser l'affichage"):
        st.session_state.resultat_ia = None
        st.rerun()

# --- ZONE DE SAISIE ---
col_input, col_info = st.columns([2, 1])

with col_input:
    st.subheader("📍 Adresses de la tournée")
    addresses_raw = st.text_area(
        "Collez les adresses des patients (une par ligne) :",
        "10 rue de la Paix, Paris\n5 Avenue Foch, Paris\n120 Boulevard Saint-Germain, Paris",
        height=150
    )

with col_info:
    st.subheader("ℹ️ Informations")
    st.info("""
    - **Algorithme :** IA Heuristic Solver
    - **Réseau :** OSRM Real Road (Temps réel)
    - **Marqueurs :** Numérotation chronologique
    """)

# --- LOGIQUE DE CALCUL ---
if st.button("🚀 CALCULER L'ITINÉRAIRE OPTIMAL"):
    if not api_key:
        st.error("⚠️ Veuillez entrer votre clé API dans la barre latérale.")
    else:
        # Nettoyage des adresses
        addr_list = [a.strip() for a in addresses_raw.split('\n') if a.strip()]

        # Préparation du JSON pour l'API
        payload = [
            {"id": i + 1, "address": addr, "time_window_start": 0, "time_window_end": 480}
            for i, addr in enumerate(addr_list)
        ]
        headers = {"X-API-KEY": api_key}

        with st.spinner("L'IA calcule le trajet le plus court..."):
            try:
                # Utilisation de l'URL configurée dans la sidebar
                target_url = f"{api_url.rstrip('/')}/v1/optimize"
                response = requests.post(target_url, json=payload, headers=headers, timeout=15)

                if response.status_code == 200:
                    st.session_state.resultat_ia = response.json()
                elif response.status_code == 401:
                    st.error("❌ Clé API invalide.")
                else:
                    st.error(f"Erreur {response.status_code} : {response.text}")
            except Exception as e:
                st.error(f"Impossible de joindre le serveur IA ({api_url}). Vérifiez qu'il est bien lancé.")

# --- AFFICHAGE DES RÉSULTATS ---
if st.session_state.resultat_ia:
    data = st.session_state.resultat_ia

    st.markdown("---")
    st.success(f"✅ Tournée optimisée : **{data['total_travel_time']} min** de conduite au total.")

    res_left, res_right = st.columns([1, 2])

    with res_left:
        st.subheader("📋 Feuille de route")
        steps = data['readable_route']
        segments = data['segments']

        for i in range(len(steps)):
            # Icone : Maison pour le début/fin, Point pour les patients
            icon = "🏠" if (i == 0 or i == len(steps) - 1) else "📍"
            st.markdown(f"**{i}. {icon} {steps[i]}**")

            # Affichage du temps entre les étapes
            if i < len(segments):
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🖤 *Trajet : {segments[i]} min*")

    with res_right:
        st.subheader("🗺️ Carte Interactive")
        gps_points = data['gps_coords']

        # Initialisation de la carte centrée sur le point de départ
        m = folium.Map(location=gps_points[0], zoom_start=13, tiles="cartodbpositron")

        # 1. Tracé de la route en noir (PolyLine)
        folium.PolyLine(gps_points, color="black", weight=4, opacity=0.7).add_to(m)

        # 2. Ajout des marqueurs pastilles numérotées
        for i, (lat, lon) in enumerate(gps_points):
            # Couleur distinctive pour le Cabinet
            bg_color = "#e74c3c" if (i == 0 or i == len(gps_points) - 1) else "#3498db"

            folium.Marker(
                [lat, lon],
                popup=f"Étape {i}: {steps[i]}",
                icon=DivIcon(
                    icon_size=(30, 30),
                    icon_anchor=(15, 15),
                    html=f"""
                        <div style="
                            font-family: Arial, sans-serif; 
                            color: white; 
                            background-color: {bg_color}; 
                            border-radius: 50%; 
                            width: 26px; 
                            height: 26px; 
                            display: flex; 
                            justify-content: center; 
                            align-items: center; 
                            font-weight: bold;
                            border: 2px solid white;
                            box-shadow: 0px 2px 4px rgba(0,0,0,0.3);
                        ">{i}</div>
                    """
                )
            ).add_to(m)

        # Rendu de la carte
        st_folium(m, width=800, height=500, key="map_final")

st.markdown("---")
st.caption("© 2026 IDEL Smart Optimizer - Infrastructure Cloud-Ready")