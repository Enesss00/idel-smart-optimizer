import requests
import json

# URL du serveur local (doit être lancé via main.py)
URL = "http://127.0.0.1:8000/v1/optimize"

# Scenario de test : 3 patients avec contraintes horaires à Paris
payload = [
    {
        "id": 1,
        "address": "10 rue de la Paix, Paris",
        "time_window_start": 30,  # Rendez-vous après 08:30
        "time_window_end": 120  # Avant 10:00
    },
    {
        "id": 2,
        "address": "5 Avenue Foch, Paris",
        "time_window_start": 0,  # Disponible dès 08:00
        "time_window_end": 60  # Avant 09:00
    },
    {
        "id": 3,
        "address": "120 Boulevard Saint-Germain, Paris",
        "time_window_start": 60,  # Entre 09:00
        "time_window_end": 180  # et 11:00
    }
]


def test_optimization_engine():
    print("Envoi de la requete au moteur d'optimisation...")
    try:
        response = requests.post(URL, json=payload)

        if response.status_code == 200:
            result = response.json()
            print("\nOPTIMISATION TERMINEE")
            print(f"Temps de trajet total estime : {result['total_travel_time']} minutes")
            print("\nORDRE DE PASSAGE OPTIMISE :")
            for i, etape in enumerate(result['readable_route']):
                print(f"  {i}. {etape}")
        else:
            print(f"Erreur {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Erreur de connexion au serveur : {e}")
        print("Verifiez que le service FastAPI est actif.")


if __name__ == "__main__":
    test_optimization_engine()