# Utiliser une image officielle Python légère
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier et installer les dépendances Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code du back-end et les fichiers du front-end
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Définir le répertoire de travail principal pour l'exécution
WORKDIR /app/backend

# Exposer le port de l'application
EXPOSE 8000

# Lancer l'application avec Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]