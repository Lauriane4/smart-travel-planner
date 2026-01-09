from fastapi import FastAPI
from typing import List
from pydantic import BaseModel

app = FastAPI() 

class Activity(BaseModel):
    name: str
    address: str
    category: str

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de planification d'activités !"}

@app.post("/optimize")
def optimize_itinerary(activities: List[Activity]):
    # Mettre la logique d'optimisation ici
    return {"status": "optimized", "plan": activities}