import requests
import math
import logging

# On configure le logger pour suivre les appels API en temps réel
logger = logging.getLogger(__name__)


class GeoLogic:
    """
    Service géo-spatial hybride :
    - Géocodage (API Adresse Gouv)
    - Routage réel (OSRM OpenStreetMap)
    """

    @staticmethod
    def get_coords(address: str):
        """Transforme l'adresse texte en [Lat, Lon] via l'API BAN."""
        url = "https://api-adresse.data.gouv.fr/search/"
        try:
            r = requests.get(url, params={"q": address, "limit": 1}, timeout=5)
            r.raise_for_status()
            data = r.json()
            if data["features"]:
                coords = data["features"][0]["geometry"]["coordinates"]
                return coords[1], coords[0]  # Format standard [Lat, Lon]
        except Exception as e:
            logger.error(f"Erreur de géocodage pour '{address}': {e}")
        return None

    @staticmethod
    def get_route_time(coord1, coord2):
        """
        Calcule le temps de trajet RÉEL par la route (en minutes).
        Prend en compte le réseau routier, les ponts et les sens uniques.
        """
        # OSRM attend le format [Lon,Lat] dans son URL
        loc = f"{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}"
        url = f"http://router.project-osrm.org/route/v1/driving/{loc}"

        try:
            # On demande uniquement la durée sans les détails d'étapes (économie de bande passante)
            r = requests.get(url, params={"overview": "false", "alternatives": "false"}, timeout=5)
            data = r.json()

            if data.get("code") == "Ok":
                # La durée est en secondes, on convertit en minutes (arrondi supérieur)
                duration_sec = data["routes"][0]["duration"]
                return math.ceil(duration_sec / 60)

            logger.warning("OSRM n'a pas pu trouver d'itinéraire entre ces points.")
        except Exception as e:
            logger.error(f"Erreur lors de l'appel OSRM : {e}")

        # Fallback de sécurité : Si le serveur de route est HS, on renvoie une valeur élevée
        # pour ne pas bloquer le solver mais signaler un problème.
        return 999

    @staticmethod
    def haversine_distance(coord1, coord2):
        """
        GARDÉ POUR LE BACKUP : Distance à vol d'oiseau (km).
        Utile si l'API OSRM est indisponible ou pour des pré-calculs rapides.
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))