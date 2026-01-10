from fastapi.testclient import TestClient
import pytest
import sys
import os   

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bienvenue sur l'API de planification d'activités !"}

def test_optimize_itinerary():
    request_data = {
        "days": 2,
        "activities": [
            {"name": "Statue of Liberty", "address": "Liberty Island", "category": "Sightseeing"},
            {"name": "Central Park", "address": "Central Park, New York, NY", "category": "Park"},
            {"name": "Metropolitan Museum of Art", "address": "1000 5th Ave, New York, NY 10028", "category": "Museum"}
        ]
    }
    response = client.post("/optimize", json=request_data)
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2   # Doit contenir 2 jours

def test_optimize_itinerary_no_addresses_found():
    request_data = {
        "days": 1,
        "activities": [
            {"name": "Unknown Place", "address": "This address does not exist", "category": "Unknown"}
        ]
    }
    response = client.post("/optimize", json=request_data)
    assert response.status_code == 200
    json_response = response.json()
    assert "status" in json_response
    assert json_response["status"] == "error"
    assert "message" in json_response
    assert json_response["message"] == "Aucune adresse n'a été trouvée. Vérifie l'orthographe."


def test_optimize_logic_and_distribution():
    """Vérifie que l'algorithme distribue bien les activités sur le nombre de jours demandé"""
    request_data = {
        "days": 3,
        "activities": [
            {"name": "A", "address": "100 5th Ave, NY", "category": "X"},
            {"name": "B", "address": "101 5th Ave, NY", "category": "X"},
            {"name": "C", "address": "Empire State Building, NY", "category": "X"},
            {"name": "D", "address": "Statue of Liberty, NY", "category": "X"},
            {"name": "E", "address": "Central Park, NY", "category": "X"},
            {"name": "F", "address": "Brooklyn Bridge, NY", "category": "X"}
        ]
    }
    response = client.post("/optimize", json=request_data)
    assert response.status_code == 200
    
    json_response = response.json()
    
    # 1. Vérifier qu'on a exactement 3 jours dans la réponse
    days_in_response = [key for key in json_response.keys() if "Day" in key]
    assert len(days_in_response) == 3
    
    # 2. Vérifier qu'aucune journée n'est vide
    for day in days_in_response:
        assert len(json_response[day]) > 0
        
    # 3. Vérifier que toutes les activités envoyées sont présentes dans le résultat
    total_activities = sum(len(json_response[day]) for day in days_in_response)
    assert total_activities == 6