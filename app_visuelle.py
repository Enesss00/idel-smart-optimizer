import streamlit as st
import requests
import folium
import urllib.parse  # Pour générer les liens Google Maps
from streamlit_folium import st_folium
from folium.features import DivIcon

# --- CONFIGURATION ---
st.set_page_config(page_title="IDEL Smart Optimizer", layout="wide", page_icon="🩺")

# Initialisation du Session State
if 'resultat_ia' not in st.session_state:
    st.session_state.resultat_ia = None

st.title("🩺 IDEL Smart Optimizer v1.1")
st.markdown("---")

# --- SIDEBAR : CONFIGURATION ---
with st.sidebar:
    st.header("🔑 Accès Premium")
    # Tu peux mettre ta clé par défaut ici si tu es le seul utilisateur
    api_key = st.text_input("Clé API Business", value="431134ba-a117-43d1-ba53-be32034de62c", type="password")

    st.header("⚙️ Paramètres")
    depot = st.text_input("Adresse du Cabinet", "1 rue de Rivoli, Paris")

    st.markdown("---")
    st.header("🌐 Connexion Serveur")
    # MISE À JOUR : Ton adresse Render est maintenant celle par défaut
    api_url = st.text_input("URL de l'IA Engine", "https://api-idel-engine.onrender.com")

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
    - **Réseau :** OSRM Real Road
    - **GPS :** Cliquez sur 'Naviguer' pour lancer le trajet.
    """)

# --- LOGIQUE DE CALCUL ---
if st.button("🚀 CALCULER L'ITINÉRAIRE OPTIMAL"):
    if not api_key:
        st.error("⚠️ Veuillez entrer votre clé API.")
    else:
        # On ajoute le cabinet au début de la liste pour l'IA
        addr_list = [depot] + [a.strip() for a in addresses_raw.split('\n') if a.strip()]

        payload = [
            {"id": i, "address": addr, "time_window_start": 0, "time_window_end": 720}
            for i, addr in enumerate(addr_list)
        ]
        headers = {"X-API-KEY": api_key}

        with st.spinner("L'IA calcule le trajet le plus court..."):
            try:
                target_url = f"{api_url.rstrip('/')}/v1/optimize"
                response = requests.post(target_url, json=payload, headers=headers, timeout=20)

                if response.status_code == 200:
                    st.session_state.resultat_ia = response.json()
                else:
                    st.error(f"Erreur {response.status_code} : {response.text}")
            except Exception as e:
                st.error(f"Serveur injoignable. Le premier démarrage peut prendre 30s sur Render.")

# --- AFFICHAGE DES RÉSULTATS ---
if st.session_state.resultat_ia:
    data = st.session_state.resultat_ia
    st.markdown("---")
    st.success(f"✅ Tournée optimisée : **{data['total_travel_time']} min** de conduite.")

    res_left, res_right = st.columns([1, 2])

    with res_left:
        st.subheader("📋 Feuille de route")
        steps = data['readable_route']
        segments = data['segments'] if 'segments' in data else []

        for i in range(len(steps)):
            is_cabinet = (i == 0 or i == len(steps) - 1)
            icon = "🏠" if is_cabinet else "📍"

            # Création du lien Google Maps pour la navigation
            query = urllib.parse.quote(steps[i])
            maps_url = f"https://www.google.com/maps/search/?api=1&query={query}"

            # Affichage de l'étape avec bouton GPS
            col_step, col_gps = st.columns([4, 1])
            with col_step:
                st.markdown(f"**{i}. {icon} {steps[i]}**")
            with col_gps:
                st.link_button("🚗 GPS", maps_url)

            if i < len(segments):
                st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;🖤 Trajet : {segments[i]} min")

    with res_right:
        st.subheader("🗺️ Carte Interactive")
        gps_points = data['gps_coords']
        m = folium.Map(location=gps_points[0], zoom_start=13, tiles="cartodbpositron")

        folium.PolyLine(gps_points, color="black", weight=4, opacity=0.7).add_to(m)

        for i, (lat, lon) in enumerate(gps_points):
            bg_color = "#e74c3c" if (i == 0 or i == len(gps_points) - 1) else "#3498db"
            folium.Marker(
                [lat, lon],
                popup=steps[i],
                icon=DivIcon(
                    icon_size=(30, 30),
                    icon_anchor=(15, 15),
                    html=f"""<div style="font-family: Arial; color: white; background-color: {bg_color}; 
                            border-radius: 50%; width: 26px; height: 26px; display: flex; 
                            justify-content: center; align-items: center; font-weight: bold;
                            border: 2px solid white; box-shadow: 0px 2px 4px rgba(0,0,0,0.3);">{i}</div>"""
                )
            ).add_to(m)

        st_folium(m, width=800, height=500, key="map_final")

st.markdown("---")
st.caption("© 2026 IDEL Smart Optimizer - Système de routage professionnel")