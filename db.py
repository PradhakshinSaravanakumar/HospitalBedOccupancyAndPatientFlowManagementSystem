import os
import pymongo

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = 'hospital_db'

_client = None

def get_db():
    global _client
    if _client is None:
        _client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client[DB_NAME]

def init_db():
    db = get_db()
    # Create indexes for optimal query performance
    db.users.create_index('email', unique=True)
    db.patients.create_index('mrn', unique=True)
    db.beds.create_index('bed_number', unique=True)
    db.wards.create_index('id', unique=True)
    print("MongoDB hospital_db indexes initialized successfully.")

if __name__ == '__main__':
    init_db()
