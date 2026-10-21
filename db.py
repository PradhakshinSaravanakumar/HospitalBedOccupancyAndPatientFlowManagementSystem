import os
import re
import pymongo

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_URI = 'mongodb+srv://pradhakshinasaravanakumar10_db_user:V6YmrEU0G7vzv6SF@cluster0.lfqvjin.mongodb.net/'
MONGO_URI = os.getenv('MONGO_URI', DEFAULT_URI)
DB_NAME = os.getenv('DB_NAME', 'hospital_db')

# Auto-sanitize if user retains angle brackets around password: e.g. :<password>@
MONGO_URI = re.sub(r':<([^>]+)>@', r':\1@', MONGO_URI)

_client = None

def get_masked_uri():
    """Return MongoDB URI with password redacted for safe logging."""
    return re.sub(r':([^@:]+)@', r':***@', MONGO_URI)

def get_db():
    global _client
    if _client is None:
        _client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    return _client[DB_NAME]

def init_db():
    db = get_db()
    # Create indexes for optimal query performance
    db.users.create_index('email', unique=True)
    db.patients.create_index('mrn', unique=True)
    db.beds.create_index('bed_number', unique=True)
    db.wards.create_index('id', unique=True)
    print(f"MongoDB '{DB_NAME}' indexes initialized successfully on {get_masked_uri()}.")

if __name__ == '__main__':
    init_db()
