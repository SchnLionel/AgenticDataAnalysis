from backend.db.database import engine, Base
from backend.db.models import User, Dataset, AnalysisSession, Message, Visualization

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()
