from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
import uvicorn

# --- MODULES DE SÉCURITÉ ---
from auth import verify_api_key
from database import User

# --- MODULES MÉTIER ---
from solver import RouteSolver
from geo_logic import GeoLogic

# Configuration
CABINET_ADDRESS = "1 rue de Rivoli, Paris"


# --- MODÈLES DE DONNÉES ---
class Patient(BaseModel):
    id: int = Field(..., example=101)
    address: str = Field(..., example="10 rue de la Paix, Paris")
    time_window_start: int = Field(..., description="Minutes depuis 08:00")
    time_window_end: int = Field(..., description="Minutes depuis 08:00")


class OptimizationResponse(BaseModel):
    status: str
    optimal_route: List[int]
    total_travel_time: int
    readable_route: List[str]
    segments: List[int]  # Temps entre chaque point
    gps_coords: List[Tuple[float, float]]  # [lat, lon] pour le tracé de la route


# --- INITIALISATION API ---
app = FastAPI(title="IDEL Optimizer API - Business Edition")


@app.post("/v1/optimize", response_model=OptimizationResponse)
async def optimize_route(
        patients: List[Patient],
        current_user: User = Depends(verify_api_key)
):
    print(f"💰 Client : {current_user.email} lance une optimisation.")

    if not patients:
        raise HTTPException(status_code=400, detail="Liste de patients vide.")

    try:
        # 1. GÉOCODAGE & STOCKAGE DES COORDONNÉES
        locations = []
        # On commence par le cabinet
        cabinet_coords = GeoLogic.get_coords(CABINET_ADDRESS)
        locations.append(cabinet_coords)

        for p in patients:
            coords = GeoLogic.get_coords(p.address)
            if not coords:
                raise HTTPException(status_code=422, detail=f"Adresse introuvable : {p.address}")
            locations.append(coords)

        # 2. MATRICE DE TEMPS ROUTIÈRE
        size = len(locations)
        time_matrix = [[0 for _ in range(size)] for _ in range(size)]
        for i in range(size):
            for j in range(size):
                if i != j:
                    time_matrix[i][j] = GeoLogic.get_route_time(locations[i], locations[j])

        # 3. FENÊTRES HORAIRES (Cabinet 08h-20h)
        windows = [(0, 720)]
        for p in patients:
            windows.append((p.time_window_start, p.time_window_end))

        # 4. RÉSOLUTION (OR-Tools)
        solver = RouteSolver(time_matrix=time_matrix, time_windows=windows)
        raw_route = solver.solve()

        if not raw_route:
            raise HTTPException(status_code=422, detail="Aucune solution respectant les horaires.")

        # 5. MAPPING & CALCUL DES SEGMENTS
        id_mapping = {0: f"CABINET ({CABINET_ADDRESS})"}
        for i, p in enumerate(patients):
            id_mapping[i + 1] = f"ID {p.id}: {p.address}"

        segments_times = []
        ordered_gps = []

        for k in range(len(raw_route)):
            current_index = raw_route[k]
            # On stocke les coordonnées dans l'ordre de la route
            ordered_gps.append(locations[current_index])

            # On calcule le temps vers le point suivant
            if k < len(raw_route) - 1:
                next_index = raw_route[k + 1]
                time_between = time_matrix[current_index][next_index]
                segments_times.append(int(time_between))

        return {
            "status": "success",
            "optimal_route": raw_route,
            "readable_route": [id_mapping[node] for node in raw_route],
            "segments": segments_times,
            "gps_coords": ordered_gps,
            "total_travel_time": int(sum(segments_times))
        }

    except Exception as e:
        print(f"ERREUR : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du moteur.")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)