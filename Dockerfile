# 1. Utiliser une image Python légère comme base
FROM python:3.10-slim

# 2. Définir le dossier de travail dans le conteneur
WORKDIR /app

# 3. Copier le fichier des dépendances
COPY requirements.txt .

# 4. Installer les bibliothèques nécessaires
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copier tout ton code (main.py, solver.py, geo_logic.py) dans le conteneur
COPY . .

# 6. Exposer le port 8000 (celui de ton API)
EXPOSE 8000

# 7. Commande pour lancer le serveur au démarrage du conteneur
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]