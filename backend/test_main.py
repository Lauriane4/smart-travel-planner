from fastapi.testclient import TestClient
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
    assert "status" in json_response
    assert json_response["status"] == "success"
    assert "itinerary" in json_response
    assert len(json_response["itinerary"]) == 2 

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