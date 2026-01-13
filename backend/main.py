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
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


# Configuration SQL 
DATABASE_URL = "postgresql://user:pass@db:5432/travel_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Définition du modèle de données pour l'historique des plans
class ItineraryHistory(Base):
    __tablename__ = "itinerary_history"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    days = Column(Integer, nullable=False)
    activities = Column(String, nullable=False) 
    total_activities = Column(Integer, nullable=False)

Base.metadata.create_all(bind=engine)


# Initialisation de l'application FastAPI
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
    city: str
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
            location = geolocator.geocode(activity.address + ", " + request.city)
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


    # Sauvegarde de l'itinéraire dans la base de données
    db = SessionLocal()
    itinerary_record = ItineraryHistory(
        city=request.city,
        days=n_days,
        activities=str([activity.dict() for activity in request.activities]),
        total_activities=num_activities
    )
    db.add(itinerary_record)
    db.commit()
    db.close()

    # Organisation des activités par jour
    itinerary = {}
    for day in range(n_days):
        day_activities = df[df['day_cluster'] == day]
        itinerary[f'Day {day + 1}'] = day_activities[['name', 'category', 'address', 'latitude', 'longitude']].to_dict(orient='records')

    return itinerary