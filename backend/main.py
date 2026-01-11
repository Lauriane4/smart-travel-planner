from time import sleep
from fastapi import FastAPI
from typing import List
from pydantic import BaseModel
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from sklearn.cluster import KMeans
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from k_means_constrained import KMeansConstrained

app = FastAPI() 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


geolocator = Nominatim(user_agent="travel_planner", timeout=10)

class Activity(BaseModel):
    name: str
    address: str
    category: str
    

class PlanRequest(BaseModel):
    days : int
    activities: List[Activity]

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de planification d'activités !"}

@app.post("/optimize")
def optimize_itinerary(request: PlanRequest):
    data = []

    # Géocodage des adresses
    for activity in request.activities:
        try:
            location = geolocator.geocode(activity.address + ", New York, USA")
            if location:
                data.append({
                    "name": activity.name,
                    "address": activity.address,
                    "category": activity.category,
                    "latitude": location.latitude,
                    "longitude": location.longitude
                })
            
        except GeocoderTimedOut:
                continue
    if not data:
        return {"status": "error", "message": "Aucune adresse n'a été trouvée. Vérifie l'orthographe."}
    
    # Création d'un DataFrame
    df = pd.DataFrame(data) 

    num_activities = len(df)
    n_days = request.days

    # --- LOGIQUE D'ÉQUILIBRAGE ---
    min_per_day = num_activities // n_days
    max_per_day = min_per_day + 1

    # On utilise KMeansConstrained pour forcer cette répartition
    clf = KMeansConstrained(
        n_clusters=n_days,
        size_min=min_per_day,
        size_max=max_per_day,
        random_state=0
    )
    
    df['day_cluster'] = clf.fit_predict(df[['latitude', 'longitude']])

    # Organisation des activités par jour
    itinerary = {}
    for day in range(n_days):
        day_activities = df[df['day_cluster'] == day]
        itinerary[f'Day {day + 1}'] = day_activities[['name', 'category', 'address']].to_dict(orient='records')

    return itinerary