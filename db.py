import os
import re
import pymongo

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import certifi
    CA_FILE = certifi.where()
except Exception:
    CA_FILE = None

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
        client_kwargs = {
            'serverSelectionTimeoutMS': 15000,
            'connectTimeoutMS': 15000,
            'socketTimeoutMS': 15000
        }
        if CA_FILE:
            client_kwargs['tlsCAFile'] = CA_FILE
        _client = pymongo.MongoClient(MONGO_URI, **client_kwargs)
    return _client[DB_NAME]

def init_db():
    try:
        db = get_db()
        # Create indexes for optimal query performance
        db.users.create_index('email', unique=True)
        db.patients.create_index('mrn', unique=True)
        db.beds.create_index('bed_number', unique=True)
        db.wards.create_index('id', unique=True)
        print(f"MongoDB '{DB_NAME}' indexes initialized successfully on {get_masked_uri()}.")
    except Exception as e:
        print(f"[MongoDB Warning] Could not initialize indexes: {e}")
        print("Note: If running on cloud (Render), ensure '0.0.0.0/0' is added to MongoDB Atlas Network Access.")

if __name__ == '__main__':
    init_db()
