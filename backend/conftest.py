import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch

# Créer une BD SQLite dans un fichier temporaire pour les tests
db_fd, db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

from main import app, get_db, Base, engine

# Créer les tables sur l'engine 
Base.metadata.create_all(bind=engine)

@pytest.fixture(autouse=True, scope="function")
def override_db_dependency():
    """Override la dépendance DB avec une vraie session"""
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=engine)
    
    def fake_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = fake_get_db
    yield
    app.dependency_overrides = {}


@pytest.fixture(autouse=True, scope="function")
def mock_geocode():
    """Mock le geocodage pour éviter les appels réseau"""
    with patch("main.geolocator.geocode") as mock:
        mock.return_value = MagicMock(
            latitude=48.8566,
            longitude=2.3522
        )
        yield mock


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Cleanup le fichier temporaire après les tests"""
    yield
    try:
        os.close(db_fd)
        os.unlink(db_path)
    except:
        pass

