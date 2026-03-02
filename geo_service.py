import requests
import logging

logger = logging.getLogger(__name__)


class GeoService:
    """
    Service de traitement des données géographiques.
    Utilise l'API Base Adresse Nationale (BAN) pour le géocodage.
    """

    @staticmethod
    def get_coordinates(address: str):
        """
        Convertit une chaîne de caractères (adresse) en coordonnées GPS [lat, lon].
        Source: api-adresse.data.gouv.fr (Gratuit, Haute Disponibilité)
        """
        url = "https://api-adresse.data.gouv.fr/search/"
        params = {"q": address, "limit": 1}

        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data['features']:
                # L'API renvoie [longitude, latitude], on inverse pour le standard GPS
                lon, lat = data['features'][0]['geometry']['coordinates']
                return lat, lon

            logger.warning(f"Adresse non trouvée : {address}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors du géocodage de {address}: {e}")
            return None