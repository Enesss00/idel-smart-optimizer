import streamlit as st
import requests
import folium
import urllib.parse
from streamlit_folium import st_folium
from folium.features import DivIcon

# --- CONFIGURATION ---
st.set_page_config(page_title="IDEL Smart Optimizer", layout="wide", page_icon="🩺")

# Initialisation du Session State
if 'resultat_ia' not in st.session_state:
    st.session_state.resultat_ia = None


# --- FONCTION EXPORT WHATSAPP ---
def generer_lien_whatsapp(steps, temps_total):
    texte = f"🩺 *MA TOURNÉE OPTIMISÉE* 🩺\n\n⏱ Temps de route : {temps_total} min\n\n"
    for i, adresse in enumerate(steps):
        emoji = "🏠" if (i == 0 or i == len(steps) - 1) else "📍"
        texte += f"{i}. {emoji} {adresse}\n"

    texte_encode = urllib.parse.quote(texte)
    return f"https://wa.me/?text={texte_encode}"


st.title("🩺 IDEL Smart Optimizer v1.1 - Mode Premium")
st.markdown("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Accès Premium")
    api_key = st.text_input("Clé API Business", value="431134ba-a117-43d1-ba53-be32034de62c", type="password")

    st.header("⚙️ Paramètres")
    depot = st.text_input("Adresse du Cabinet", "1 rue de Rivoli, Paris")

    st.markdown("---")
    st.header("🌐 Connexion Serveur")
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
    st.subheader("ℹ️ Aide à la navigation")
    st.success("""
    - **Google Maps :** Idéal pour la vue satellite.
    - **Waze :** Idéal pour éviter les bouchons.
    - **WhatsApp :** Pour envoyer la liste à un(e) remplaçant(e).
    """)

# --- LOGIQUE DE CALCUL ---
if st.button("🚀 CALCULER L'ITINÉRAIRE OPTIMAL"):
    if not api_key:
        st.error("⚠️ Veuillez entrer votre clé API.")
    else:
        addr_list = [depot] + [a.strip() for a in addresses_raw.split('\n') if a.strip()]
        payload = [{"id": i, "address": addr, "time_window_start": 0, "time_window_end": 720} for i, addr in
                   enumerate(addr_list)]
        headers = {"X-API-KEY": api_key}

        with st.spinner("L'IA calcule le trajet..."):
            try:
                target_url = f"{api_url.rstrip('/')}/v1/optimize"
                response = requests.post(target_url, json=payload, headers=headers, timeout=20)
                if response.status_code == 200:
                    st.session_state.resultat_ia = response.json()
                else:
                    st.error(f"Erreur {response.status_code}")
            except:
                st.error("Serveur en pause (Render). Réessayez dans 30 secondes.")

# --- AFFICHAGE DES RÉSULTATS ---
if st.session_state.resultat_ia:
    data = st.session_state.resultat_ia
    steps = data['readable_route']

    st.markdown("---")

    # BOUTON WHATSAPP (Ligne entière)
    lien_wa = generer_lien_whatsapp(steps, data['total_travel_time'])
    st.link_button("📲 Partager la liste sur WhatsApp (Remplaçant, Collègue...)", lien_wa, use_container_width=True)

    res_left, res_right = st.columns([1, 2])

    with res_left:
        st.subheader("📋 Feuille de route")
        for i, adresse in enumerate(steps):
            is_cab = (i == 0 or i == len(steps) - 1)
            emoji = "🏠" if is_cab else "📍"

            # Liens de navigation
            query = urllib.parse.quote(adresse)
            google_url = f"https://www.google.com/maps/search/?api=1&query={query}"
            waze_url = f"https://waze.com/ul?q={query}&navigate=yes"

            with st.container(border=True):
                st.markdown(f"**{i}. {emoji} {adresse}**")
                c1, c2 = st.columns(2)
                c1.link_button("🚗 Google", google_url, use_container_width=True)
                c2.link_button("🚙 Waze", waze_url, use_container_width=True)

    with res_right:
        st.subheader("🗺️ Carte Interactive")
        gps_points = data['gps_coords']
        m = folium.Map(location=gps_points[0], zoom_start=13, tiles="cartodbpositron")
        folium.PolyLine(gps_points, color="black", weight=4, opacity=0.7).add_to(m)
        for i, (lat, lon) in enumerate(gps_points):
            bg = "#e74c3c" if (i == 0 or i == len(gps_points) - 1) else "#3498db"
            folium.Marker([lat, lon], icon=DivIcon(icon_size=(30, 30),
                                                   html=f'<div style="background:{bg};color:white;border-radius:50%;width:25px;height:25px;display:flex;justify-content:center;align-items:center;font-weight:bold;border:2px solid white;">{i}</div>')).add_to(
                m)
        st_folium(m, width=800, height=600, key="map_v1")

st.caption("© 2026 IDEL Smart Optimizer - Option 1 : Navigation Premium")