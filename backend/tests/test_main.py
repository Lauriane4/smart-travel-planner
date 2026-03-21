from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
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
        "city": "New York",
        "activities": [
            {"name": "Statue of Liberty", "address": "Liberty Island", "category": "Sightseeing"},
            {"name": "Central Park", "address": "Central Park, New York, NY", "category": "Park"},
            {"name": "Metropolitan Museum of Art", "address": "1000 5th Ave, New York, NY 10028", "category": "Museum"}
        ]
    }
    response = client.post("/optimize", json=request_data)
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2   
    assert set(json_response.keys()) == {"Day 1", "Day 2"}


def test_optimize_itinerary_no_addresses_found():
    request_data = {
        "days": 1,
        "city": "Nowhere",
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
        "city": "New York",
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

def test_history_endpoint(mock_geocode):
    # Génère un itinéraire
    client.post("/optimize", json={
        "days": 1,
        "city": "Paris",
        "activities": [
            {"name": "Louvre", "address": "Louvre Museum", "category": "Museum"}
        ]
    })

    response = client.get("/history")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    itin = data[0]
    assert "city" in itin
    assert "activities" in itin
    assert "created_at" in itin

def test_activity_schema_in_response(mock_geocode):
    response = client.post("/optimize", json={
        "days": 1,
        "city": "Paris",
        "activities": [
            {"name": "Louvre", "address": "Louvre Museum", "category": "Museum"}
        ]
    })

    assert response.status_code == 200
    data = response.json()

    day = data["Day 1"][0]

    assert "name" in day
    assert "address" in day
    assert "category" in day
    assert "latitude" in day
    assert "longitude" in day

    assert isinstance(day["latitude"], float)
    assert isinstance(day["longitude"], float)

def test_single_day_itinerary(mock_geocode):
    response = client.post("/optimize", json={
        "days": 1,
        "city": "Paris",
        "activities": [
            {"name": "Louvre", "address": "Louvre Museum", "category": "Museum"},
            {"name": "Orsay", "address": "Musée d'Orsay", "category": "Museum"}
        ]
    })

    assert response.status_code == 200
    data = response.json()

    assert list(data.keys()) == ["Day 1"]
    assert len(data["Day 1"]) == 2

def test_more_days_than_activities(mock_geocode):
    response = client.post("/optimize", json={
        "days": 5,
        "city": "Paris",
        "activities": [
            {"name": "Louvre", "address": "Louvre Museum", "category": "Museum"},
            {"name": "Orsay", "address": "Musée d'Orsay", "category": "Museum"}
        ]
    })

    assert response.status_code == 200
    data = response.json()

    # On ne doit pas avoir plus de jours que d'activités utiles
    non_empty_days = [day for day in data if len(data[day]) > 0]
    assert len(non_empty_days) <= 2

def test_history_returns_recent_only(mock_geocode):
    response = client.get("/history")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    from datetime import datetime, timedelta

    for itin in data:
        created_at = datetime.fromisoformat(itin["created_at"])
        assert created_at >= datetime.utcnow() - timedelta(days=5)

def test_history_empty_db():
    response = client.get("/history")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    
def test_invalid_payload():
    response = client.post("/optimize", json={
        "days": "two",
        "city": "Paris",
        "activities": []
    })

    assert response.status_code == 422
