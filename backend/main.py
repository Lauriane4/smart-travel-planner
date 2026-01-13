import json
from time import sleep
from click import DateTime
from fastapi import FastAPI, Depends
from typing import List
from pydantic import BaseModel
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from sklearn.cluster import KMeans
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from k_means_constrained import KMeansConstrained
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, timedelta

# Initialisation de l'application FastAPI
app = FastAPI() 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration SQL 
DATABASE_URL = "postgresql://user:pass@db:5432/travel_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Définition du modèle de données pour l'historique des plans
class ItineraryHistory(Base):
    __tablename__ = "itinerary"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    days = Column(Integer, nullable=False)
    activities_json = Column(String, nullable=False)  # Stocke les activités sous forme de chaîne JSON
    total_activities = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)

class Activity(Base):
    __tablename__ = "activity"
    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itinerary.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    day_assigned = Column(Integer, nullable=False)

   
Base.metadata.create_all(bind=engine)


geolocator = Nominatim(user_agent="travel_planner", timeout=10)

class ActivitySchema(BaseModel):
    name: str
    address: str
    category: str
    

class PlanRequest(BaseModel):
    days : int
    city: str
    activities: List[ActivitySchema]

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
        activities_json=json.dumps(data),
        total_activities=num_activities,
        created_at=datetime.utcnow()
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

@app.get("/history")
def get_history():
    db = SessionLocal()
    try:
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        records = db.query(ItineraryHistory)\
        .filter(ItineraryHistory.created_at >= five_days_ago)\
        .order_by(ItineraryHistory.created_at.desc())\
        .all()

        history_list = []
        for itin in records:
            history_list.append({
                "id": itin.id,
                "city": itin.city,
                "days": itin.days,
                "activities": itin.activities_json if hasattr(itin, 'activities_json') else "[]",
                "created_at": itin.created_at.isoformat()
            })
        return history_list 
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique : {e}")
        return []
    finally:
        db.close()