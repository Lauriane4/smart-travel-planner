# 🗽 Smart Travel Planner - NYC

Un planificateur d'itinéraire intelligent qui utilise l'algorithme **K-Means** pour regrouper les activités par zone géographique et optimiser les déplacements quotidiens à New York.

## Stack Technique
- **Backend :** Python (FastAPI), Scikit-Learn (K-Means), Pandas, Geopy.
- **Frontend :** HTML5, JavaScript (ES6), CSS3.
- **DevOps :** Docker, Docker Compose, GitHub Actions (CI).

## Pipeline CI/CD
Ce projet intègre une chaîne d'intégration continue automatisée via **GitHub Actions** qui effectue :
1. **Linting Python (Flake8)** : Vérification de la conformité du code backend.
2. **Linting JS (ESLint)** : Validation des standards du code frontend.
3. **Tests Unitaires (Pytest)** : Validation de la logique de calcul de l'API.
4. **Build Docker** : Vérification de la construction des images pour garantir la portabilité.

## Installation et Lancement
Assurez-vous d'avoir **Docker** et **Docker Compose** installés.

```bash
# Cloner le projet
git clone https://github.com/Lauriane4/smart-travel-planner.git

# Lancer l'application
docker-compose up --build

```

L'application est ensuite accessible sur http://localhost.

## Objectifs DevOps accomplis
- Conteneurisation multi-services.

- Automatisation de la qualité du code (Linting).

- Pipeline d'intégration continue (CI).

- Séparation des responsabilités (SOC) entre Front et Back.