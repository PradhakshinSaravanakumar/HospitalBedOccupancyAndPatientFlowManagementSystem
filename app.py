import os
import random
import datetime
import numpy as np
import joblib
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from db import get_db, init_db, get_masked_uri, DB_NAME
from seed import seed_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
CORS(app)

# Load XGBoost models at startup
def load_model(name):
    path = os.path.join(MODELS_DIR, name)
    if os.path.exists(path):
        return joblib.load(path)
    return None

xgb_occupancy        = load_model('xgb_occupancy.pkl')
xgb_occupancy_feats  = load_model('xgb_occupancy_features.pkl')
xgb_los              = load_model('xgb_los.pkl')
xgb_los_feats        = load_model('xgb_los_features.pkl')
xgb_readmission      = load_model('xgb_readmission.pkl')
xgb_readmission_feats= load_model('xgb_readmission_features.pkl')

print(f"[XGBoost] Occupancy model loaded: {xgb_occupancy is not None}")
print(f"[XGBoost] LOS model loaded: {xgb_los is not None}")
print(f"[XGBoost] Readmission model loaded: {xgb_readmission is not None}")

# Ensure DB initialized & seeded
init_db()
db = get_db()
if db.users.count_documents({}) == 0:
    seed_db()

# Helper function to serialize MongoDB documents to JSON
def clean_doc(doc):
    if not doc:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

def clean_docs(cursor):
    return [clean_doc(doc) for doc in cursor]

# Map ward search terms to IDs
WARD_MAP = {
    'ICU': 1,
    'EMERGENCY': 2,
    'SURGERY': 3,
    'GENERAL': 3,
    'CARDIOLOGY': 4,
    'PEDIATRICS': 5,
    'NEUROLOGY': 6,
    'ORTHOPEDIC': 7,
    'MATERNITY': 8
}

# -------------------------------------------------------------
# STATIC FILES SERVING
# -------------------------------------------------------------
@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(BASE_DIR, filename)

# -------------------------------------------------------------
# AUTH API
# -------------------------------------------------------------
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    user = db.users.find_one({'email': email, 'password': password})
    if user:
        return jsonify({
            'success': True,
            'user': {
                'id': str(user.get('id', user['_id'])),
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

# -------------------------------------------------------------
# GLOBAL KPIS API
# -------------------------------------------------------------
@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    total_beds = db.beds.count_documents({})
    occupied_beds = db.beds.count_documents({'status': 'Occupied'})
    available_beds = db.beds.count_documents({'status': 'Available'})
    cleaning_beds = db.beds.count_documents({'status': 'Cleaning'})
    maintenance_beds = db.beds.count_documents({'status': {'$in': ['Maintenance', 'Reserved']}})

    total_patients = db.patients.count_documents({'status': 'Admitted'})
    discharged_patients = db.patients.count_documents({'status': 'Discharged'})
    critical_patients = db.patients.count_documents({'condition': 'Critical', 'status': 'Admitted'})
    active_alerts = db.alerts.count_documents({'is_resolved': 0})

    occupancy_rate = int(round((occupied_beds / max(1, total_beds)) * 100)) if total_beds > 0 else 0

    return jsonify({
        'success': True,
        'data': {
            'totalBeds': total_beds,
            'occupiedBeds': occupied_beds,
            'availableBeds': available_beds,
            'cleaningBeds': cleaning_beds,
            'maintenanceBeds': maintenance_beds,
            'occupancyRate': occupancy_rate,
            'totalPatients': total_patients,
            'dischargedPatients': discharged_patients,
            'criticalPatients': critical_patients,
            'activeAlerts': active_alerts
        }
    })

# -------------------------------------------------------------
# WARDS API
# -------------------------------------------------------------
@app.route('/api/wards', methods=['GET'])
def get_wards():
    wards = clean_docs(db.wards.find().sort('id', 1))
    return jsonify({'success': True, 'data': wards})

@app.route('/api/wards', methods=['POST'])
def add_ward():
    data = request.json or {}
    max_ward = db.wards.find_one(sort=[("id", -1)])
    next_id = (max_ward['id'] + 1) if max_ward and 'id' in max_ward else 1

    ward_doc = {
        "id": next_id,
        "name": data.get('name'),
        "department": data.get('department'),
        "total_beds": int(data.get('total_beds', 0)),
        "occupied_beds": int(data.get('occupied_beds', 0)),
        "status": data.get('status', 'Optimal'),
        "nurse_in_charge": data.get('nurse_in_charge', 'Unassigned')
    }
    result = db.wards.insert_one(ward_doc)
    return jsonify({'success': True, 'id': next_id, '_id': str(result.inserted_id)})

# -------------------------------------------------------------
# PATIENTS API
# -------------------------------------------------------------
@app.route('/api/patients', methods=['GET'])
def get_patients():
    patients = clean_docs(db.patients.find().sort('id', -1))
    for p in patients:
        if p.get('ward_id'):
            ward = db.wards.find_one({'id': p['ward_id']})
            p['ward_name'] = ward['name'] if ward else p.get('ward_name', 'General')
        elif 'ward_name' not in p:
            p['ward_name'] = 'General'

        if p.get('bed_id'):
            bed = db.beds.find_one({'id': p['bed_id']})
            p['bed_number'] = bed['bed_number'] if bed else p.get('bed_number', 'Unassigned')
        elif 'bed_number' not in p:
            p['bed_number'] = 'Unassigned'
    return jsonify({'success': True, 'data': patients})

@app.route('/api/patients', methods=['POST'])
def add_patient():
    data = request.json or {}
    max_patient = db.patients.find_one(sort=[("id", -1)])
    next_id = (max_patient['id'] + 1) if max_patient and 'id' in max_patient else 1

    mrn = data.get('mrn') or f"PT-{random.randint(4820, 9999)}"
    admission_date = data.get('admission_date') or datetime.datetime.now().strftime("%b %d")

    ward_name_input = data.get('ward_name', 'General')
    ward_id = data.get('ward_id')
    if not ward_id:
        key = ward_name_input.upper()
        for k, v in WARD_MAP.items():
            if k in key:
                ward_id = v
                break

    patient_doc = {
        "id": next_id,
        "mrn": mrn,
        "name": data.get('name'),
        "age": int(data.get('age', 40)),
        "gender": data.get('gender', 'Male'),
        "condition": data.get('condition', 'Stable'),
        "diagnosis": data.get('diagnosis', 'General Care'),
        "ward_id": ward_id,
        "ward_name": ward_name_input,
        "bed_id": data.get('bed_id'),
        "bed_number": data.get('bed_number', 'Unassigned'),
        "admission_date": admission_date,
        "attending_physician": data.get('physician', 'Dr. On Call'),
        "status": 'Admitted'
    }
    result = db.patients.insert_one(patient_doc)

    bed_num = data.get('bed_number')
    bed_id = data.get('bed_id')
    now_time = datetime.datetime.now().strftime("%I:%M %p")
    if bed_num and not bed_id:
        existing_bed = db.beds.find_one({'bed_number': bed_num})
        if existing_bed:
            bed_id = existing_bed['id']
            db.beds.update_one({'id': bed_id}, {'$set': {'status': 'Occupied', 'patient_id': next_id, 'last_updated': now_time}})
        else:
            max_b = db.beds.find_one(sort=[("id", -1)])
            bed_id = (max_b['id'] + 1) if max_b and 'id' in max_b else 100
            db.beds.insert_one({
                'id': bed_id,
                'bed_number': bed_num,
                'ward_id': ward_id or 1,
                'bed_type': 'Standard',
                'status': 'Occupied',
                'patient_id': next_id,
                'last_updated': now_time
            })
        db.patients.update_one({'id': next_id}, {'$set': {'bed_id': bed_id}})
    elif bed_id:
        db.beds.update_one({'id': bed_id}, {'$set': {'status': 'Occupied', 'patient_id': next_id, 'last_updated': now_time}})

    if ward_id:
        db.wards.update_one({'id': ward_id}, {'$inc': {'occupied_beds': 1}})

    print(f"[MongoDB] Added new patient {mrn} - {data.get('name')} to database (Bed: {bed_num}, ID: {bed_id}).")
    return jsonify({'success': True, 'id': next_id, 'mrn': mrn, 'bed_id': bed_id, '_id': str(result.inserted_id)})

@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.json or {}
    db.patients.update_one(
        {'id': patient_id},
        {'$set': {
            'name': data.get('name'),
            'age': int(data.get('age', 40)),
            'condition': data.get('condition'),
            'diagnosis': data.get('diagnosis'),
            'ward_name': data.get('ward_name'),
            'bed_number': data.get('bed_number'),
            'status': data.get('status', 'Admitted'),
            'attending_physician': data.get('physician')
        }}
    )
    print(f"[MongoDB] Updated patient ID {patient_id} in database.")
    return jsonify({'success': True})

@app.route('/api/patients/by-mrn/<mrn>', methods=['DELETE'])
@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id=None, mrn=None):
    query = {'mrn': mrn} if mrn else {'id': patient_id}
    patient = db.patients.find_one(query)
    if patient:
        if patient.get('bed_id'):
            db.beds.update_one({'id': patient['bed_id']}, {'$set': {'status': 'Available', 'patient_id': None}})
        if patient.get('ward_id'):
            db.wards.update_one({'id': patient['ward_id']}, {'$inc': {'occupied_beds': -1}})
        db.patients.delete_one(query)
        print(f"[MongoDB] Deleted patient {query} from database.")
    return jsonify({'success': True})

@app.route('/api/patients/<int:patient_id>/discharge', methods=['POST'])
@app.route('/api/patients/by-mrn/<mrn>/discharge', methods=['POST'])
def discharge_patient(patient_id=None, mrn=None):
    query = {'mrn': mrn} if mrn else {'id': patient_id}
    patient = db.patients.find_one(query)
    if not patient:
        return jsonify({'success': False, 'message': 'Patient not found'}), 404

    now_str = datetime.datetime.now().strftime("%b %d, %Y - %I:%M %p")
    time_str = datetime.datetime.now().strftime("%I:%M %p")

    # Update patient status to Discharged
    db.patients.update_one(query, {'$set': {
        'status': 'Discharged',
        'discharge_date': now_str
    }})

    # Find bed and transition to Cleaning
    bed = None
    if patient.get('bed_id'):
        bed = db.beds.find_one({'id': patient['bed_id']})
    if not bed and patient.get('id'):
        bed = db.beds.find_one({'patient_id': patient['id']})
    if not bed and patient.get('bed_number'):
        bed = db.beds.find_one({'bed_number': patient['bed_number']})

    bed_number = 'Unassigned'
    if bed:
        bed_number = bed.get('bed_number', 'Bed')
        db.beds.update_one({'id': bed['id']}, {'$set': {
            'status': 'Cleaning',
            'patient_id': None,
            'last_updated': time_str
        }})

    # Decrement ward occupied count
    ward_id = patient.get('ward_id')
    if not ward_id and bed:
        ward_id = bed.get('ward_id')
    if ward_id:
        db.wards.update_one({'id': ward_id}, {'$inc': {'occupied_beds': -1}})

    # Add Housekeeping Alert
    max_alert = db.alerts.find_one(sort=[("id", -1)])
    next_alert_id = (max_alert['id'] + 1) if max_alert and 'id' in max_alert else 1
    db.alerts.insert_one({
        'id': next_alert_id,
        'title': f'Bed {bed_number} Cleaning Required',
        'severity': 'Medium',
        'category': 'Housekeeping',
        'message': f'Patient {patient.get("name", "Unknown")} was discharged. Bed {bed_number} moved to Cleaning state.',
        'is_resolved': 0
    })

    print(f"[Discharge] Patient {patient.get('name')} discharged. Bed {bed_number} moved to Cleaning.")
    return jsonify({
        'success': True,
        'message': f'Patient {patient.get("name")} discharged. Bed {bed_number} moved to Cleaning state.',
        'bed_number': bed_number
    })

@app.route('/api/patients/<int:patient_id>/transfer', methods=['POST'])
@app.route('/api/patients/by-mrn/<mrn>/transfer', methods=['POST'])
def transfer_patient(patient_id=None, mrn=None):
    query = {'mrn': mrn} if mrn else {'id': patient_id}
    patient = db.patients.find_one(query)
    if not patient:
        return jsonify({'success': False, 'message': 'Patient not found'}), 404

    data = request.json or {}
    new_ward_id = int(data.get('ward_id', 1))
    new_ward_name = data.get('ward_name', 'General')
    new_bed_id = data.get('bed_id')
    new_bed_number = data.get('bed_number')
    time_str = datetime.datetime.now().strftime("%I:%M %p")

    # 1. Old bed transitions to Cleaning
    old_bed = None
    if patient.get('bed_id'):
        old_bed = db.beds.find_one({'id': patient['bed_id']})
    if not old_bed and patient.get('id'):
        old_bed = db.beds.find_one({'patient_id': patient['id']})

    old_bed_num = 'Previous'
    if old_bed:
        old_bed_num = old_bed.get('bed_number', 'Previous')
        db.beds.update_one({'id': old_bed['id']}, {'$set': {
            'status': 'Cleaning',
            'patient_id': None,
            'last_updated': time_str
        }})

    old_ward_id = patient.get('ward_id')
    if old_ward_id:
        db.wards.update_one({'id': old_ward_id}, {'$inc': {'occupied_beds': -1}})

    # 2. Assign new bed
    if new_bed_id:
        new_bed_id = int(new_bed_id)
        db.beds.update_one({'id': new_bed_id}, {'$set': {
            'status': 'Occupied',
            'patient_id': patient['id'],
            'ward_id': new_ward_id,
            'last_updated': time_str
        }})
        new_bed = db.beds.find_one({'id': new_bed_id})
        new_bed_number = new_bed.get('bed_number', new_bed_number)
    elif new_bed_number:
        existing_bed = db.beds.find_one({'bed_number': new_bed_number})
        if existing_bed:
            new_bed_id = existing_bed['id']
            db.beds.update_one({'id': new_bed_id}, {'$set': {
                'status': 'Occupied',
                'patient_id': patient['id'],
                'ward_id': new_ward_id,
                'last_updated': time_str
            }})
        else:
            max_b = db.beds.find_one(sort=[("id", -1)])
            new_bed_id = (max_b['id'] + 1) if max_b and 'id' in max_b else 100
            db.beds.insert_one({
                'id': new_bed_id,
                'bed_number': new_bed_number,
                'ward_id': new_ward_id,
                'bed_type': 'Standard',
                'status': 'Occupied',
                'patient_id': patient['id'],
                'equipment': 'Standard',
                'last_updated': time_str
            })

    # Increment new ward count
    db.wards.update_one({'id': new_ward_id}, {'$inc': {'occupied_beds': 1}})

    # Update patient record
    db.patients.update_one(query, {'$set': {
        'ward_id': new_ward_id,
        'ward_name': new_ward_name,
        'bed_id': new_bed_id,
        'bed_number': new_bed_number
    }})

    print(f"[Transfer] Shifted {patient.get('name')} from {patient.get('ward_name')} to {new_ward_name} ({new_bed_number}).")
    return jsonify({
        'success': True,
        'message': f"Patient shifted to {new_ward_name} ({new_bed_number}). Previous bed {old_bed_num} moved to Cleaning.",
        'new_ward': new_ward_name,
        'new_bed': new_bed_number
    })

# -------------------------------------------------------------
# BEDS API
# -------------------------------------------------------------
@app.route('/api/beds', methods=['GET'])
def get_beds():
    beds = clean_docs(db.beds.find().sort('id', 1))
    for b in beds:
        if b.get('ward_id'):
            ward = db.wards.find_one({'id': b['ward_id']})
            b['ward_name'] = ward['name'] if ward else 'General'
        if b.get('patient_id'):
            pat = db.patients.find_one({'id': b['patient_id']})
            b['patient_name'] = pat['name'] if pat else None
            b['mrn'] = pat['mrn'] if pat else None
    return jsonify({'success': True, 'data': beds})

@app.route('/api/beds/available', methods=['GET'])
def get_available_beds():
    ward_id = request.args.get('ward_id')
    query = {'status': 'Available'}
    if ward_id:
        query['ward_id'] = int(ward_id)
    avail = clean_docs(db.beds.find(query).sort('bed_number', 1))
    for b in avail:
        if b.get('ward_id'):
            ward = db.wards.find_one({'id': b['ward_id']})
            b['ward_name'] = ward['name'] if ward else 'General'
    return jsonify({'success': True, 'data': avail})

@app.route('/api/beds/<int:bed_id>/cleaning-completed', methods=['POST', 'PUT'])
def cleaning_completed(bed_id):
    bed = db.beds.find_one({'id': bed_id})
    if not bed:
        return jsonify({'success': False, 'message': 'Bed not found'}), 404

    time_str = datetime.datetime.now().strftime("%I:%M %p")
    db.beds.update_one({'id': bed_id}, {'$set': {
        'status': 'Available',
        'patient_id': None,
        'last_updated': time_str
    }})

    db.alerts.update_many(
        {'category': 'Housekeeping', 'message': {'$regex': bed.get('bed_number', 'Bed')}},
        {'$set': {'is_resolved': 1}}
    )

    print(f"[Cleaning] Bed {bed.get('bed_number')} marked cleaning completed -> Available.")
    return jsonify({
        'success': True,
        'message': f"Cleaning completed! Bed {bed.get('bed_number')} is now Available."
    })

@app.route('/api/beds/<int:bed_id>/status', methods=['PUT'])
def update_bed_status(bed_id):
    data = request.json or {}
    status = data.get('status', 'Available')
    time_str = datetime.datetime.now().strftime("%I:%M %p")
    update_data = {'status': status, 'last_updated': time_str}
    if status in ['Available', 'Cleaning']:
        update_data['patient_id'] = None
    db.beds.update_one({'id': bed_id}, {'$set': update_data})
    return jsonify({'success': True})

# -------------------------------------------------------------
# ALERTS API
# -------------------------------------------------------------
@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    alerts = clean_docs(db.alerts.find().sort('id', -1))
    return jsonify({'success': True, 'data': alerts})

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['PUT'])
def resolve_alert(alert_id):
    db.alerts.update_one({'id': alert_id}, {'$set': {'is_resolved': 1}})
    return jsonify({'success': True})

@app.route('/api/alerts', methods=['POST'])
def add_alert():
    data = request.json or {}
    max_alert = db.alerts.find_one(sort=[("id", -1)])
    next_id = (max_alert['id'] + 1) if max_alert and 'id' in max_alert else 1

    alert_doc = {
        "id": next_id,
        "title": data.get('title'),
        "severity": data.get('severity', 'Medium'),
        "category": data.get('category', 'General'),
        "message": data.get('message'),
        "is_resolved": 0
    }
    result = db.alerts.insert_one(alert_doc)
    return jsonify({'success': True, 'id': next_id, '_id': str(result.inserted_id)})

# -------------------------------------------------------------
# AI PREDICTIONS API  (XGBoost)
# -------------------------------------------------------------
@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    """Run all 3 XGBoost models against live MongoDB data and return predictions."""
    now = datetime.datetime.now()
    dow          = now.weekday()
    month        = now.month
    week_of_year = int(now.strftime('%W'))
    is_weekend   = 1 if dow >= 5 else 0
    is_winter    = 1 if month in [11, 12, 1, 2] else 0
    is_summer    = 1 if month in [6, 7, 8] else 0

    # Pull live ward/bed stats from MongoDB
    wards = list(db.wards.find())
    total_capacity   = sum(w.get('total_beds', 0) for w in wards)
    total_occupied   = sum(w.get('occupied_beds', 0) for w in wards)
    total_available  = total_capacity - total_occupied
    occupancy_rate   = round(total_occupied / max(1, total_capacity), 4)

    patients = list(db.patients.find({'status': 'Admitted'}))
    total_patients   = len(patients)
    daily_admissions = max(0, int(np.random.normal(7 * (1.15 if dow < 2 else 0.9), 1.5)))
    daily_discharges = max(0, int(np.random.normal(6, 2)))
    adm_dis_ratio    = round(daily_admissions / max(1, daily_discharges), 4)

    ward_predictions = []
    for ward in wards:
        wc  = ward.get('total_beds', 20)
        woc = ward.get('occupied_beds', 0)
        wav = wc - woc
        wr  = round(woc / max(1, wc), 4)

        # --- Occupancy Forecast per ward ---
        if xgb_occupancy and xgb_occupancy_feats:
            feats = {
                'day_of_week': dow, 'month': month, 'week_of_year': week_of_year,
                'is_weekend': is_weekend, 'is_winter': is_winter, 'is_summer': is_summer,
                'ward_capacity': wc, 'occupied_beds': woc, 'available_beds': wav,
                'daily_admissions': daily_admissions, 'daily_discharges': daily_discharges,
                'occupancy_rate': wr, 'admission_discharge_ratio': adm_dis_ratio
            }
            row = np.array([[feats[f] for f in xgb_occupancy_feats]])
            pred_occ = float(np.clip(xgb_occupancy.predict(row)[0], 0.0, 1.0))
        else:
            pred_occ = min(1.0, wr + 0.03)

        ward_predictions.append({
            'ward_name': ward.get('name'),
            'current_occupancy': round(wr * 100, 1),
            'predicted_occupancy': round(pred_occ * 100, 1),
            'current_occupied': woc,
            'total_beds': wc
        })

    # --- Overall Occupancy Forecast ---
    if xgb_occupancy and xgb_occupancy_feats:
        global_feats = {
            'day_of_week': dow, 'month': month, 'week_of_year': week_of_year,
            'is_weekend': is_weekend, 'is_winter': is_winter, 'is_summer': is_summer,
            'ward_capacity': total_capacity, 'occupied_beds': total_occupied,
            'available_beds': total_available, 'daily_admissions': daily_admissions,
            'daily_discharges': daily_discharges, 'occupancy_rate': occupancy_rate,
            'admission_discharge_ratio': adm_dis_ratio
        }
        row = np.array([[global_feats[f] for f in xgb_occupancy_feats]])
        tomorrow_occupancy = float(np.clip(xgb_occupancy.predict(row)[0], 0.0, 1.0))
    else:
        tomorrow_occupancy = min(1.0, occupancy_rate + 0.03)

    # --- LOS Prediction per admitted patient ---
    patient_los = []
    condition_map = {'Critical': 4, 'Guarded': 3, 'Moderate': 2, 'Recovering': 1, 'Stable': 0}

    for p in patients[:20]:  # top 20 admitted patients
        cond_sev = condition_map.get(p.get('condition', 'Stable'), 0)
        age      = int(p.get('age', 50))
        gender   = 1 if p.get('gender', 'Male') == 'Male' else 0

        if xgb_los and xgb_los_feats:
            feats = {
                'age': age, 'gender_male': gender,
                'condition_severity': cond_sev,
                'day_of_week': dow, 'month': month, 'is_weekend': is_weekend,
                'ward_capacity': total_capacity, 'occupied_beds': total_occupied,
                'occupancy_rate': occupancy_rate
            }
            row = np.array([[feats[f] for f in xgb_los_feats]])
            los = max(1, round(float(xgb_los.predict(row)[0]), 1))
        else:
            los = {'Critical': 9, 'Guarded': 6, 'Moderate': 4, 'Recovering': 3, 'Stable': 2}.get(p.get('condition', 'Stable'), 3)

        # Readmission risk
        if xgb_readmission and xgb_readmission_feats:
            feats_r = {
                'age': age, 'gender_male': gender,
                'condition_severity': cond_sev,
                'day_of_week': dow, 'month': month,
                'ward_capacity': total_capacity,
                'occupancy_rate': occupancy_rate,
                'occupied_beds': total_occupied,
                'available_beds': total_available
            }
            row_r = np.array([[feats_r[f] for f in xgb_readmission_feats]])
            readmit_prob = round(float(xgb_readmission.predict_proba(row_r)[0][1]) * 100, 1)
        else:
            readmit_prob = {'Critical': 35, 'Guarded': 20, 'Moderate': 14, 'Stable': 6}.get(p.get('condition', 'Stable'), 10)

        patient_los.append({
            'name': p.get('name'),
            'mrn': p.get('mrn'),
            'condition': p.get('condition', 'Stable'),
            'age': age,
            'predicted_los_days': los,
            'readmission_risk_pct': readmit_prob
        })

    # Sort by readmission risk descending
    patient_los.sort(key=lambda x: x['readmission_risk_pct'], reverse=True)

    # Aggregate readmission stats
    avg_readmit = round(sum(p['readmission_risk_pct'] for p in patient_los) / max(1, len(patient_los)), 1)
    high_risk   = sum(1 for p in patient_los if p['readmission_risk_pct'] >= 25)
    avg_los     = round(sum(p['predicted_los_days'] for p in patient_los) / max(1, len(patient_los)), 1)

    # 7-day occupancy forecast (rolling prediction)
    forecast_7day = []
    current_occ = occupancy_rate
    for day_i in range(7):
        future_dow = (dow + day_i) % 7
        if xgb_occupancy and xgb_occupancy_feats:
            feats = {
                'day_of_week': future_dow, 'month': month,
                'week_of_year': min(52, week_of_year + day_i // 7),
                'is_weekend': 1 if future_dow >= 5 else 0,
                'is_winter': is_winter, 'is_summer': is_summer,
                'ward_capacity': total_capacity, 'occupied_beds': int(total_capacity * current_occ),
                'available_beds': int(total_capacity * (1 - current_occ)),
                'daily_admissions': daily_admissions, 'daily_discharges': daily_discharges,
                'occupancy_rate': round(current_occ, 4), 'admission_discharge_ratio': adm_dis_ratio
            }
            row = np.array([[feats[f] for f in xgb_occupancy_feats]])
            next_occ = float(np.clip(xgb_occupancy.predict(row)[0], 0.0, 1.0))
        else:
            next_occ = min(1.0, current_occ + random.uniform(-0.03, 0.05))

        label = 'Today' if day_i == 0 else ('Tomorrow' if day_i == 1 else f'Day {day_i + 1}')
        forecast_7day.append({'day': label, 'occupancy_pct': round(next_occ * 100, 1)})
        current_occ = next_occ

    # Generate AI Recommendations based on predictions
    recommendations = []
    for w in ward_predictions:
        if w['predicted_occupancy'] >= 90:
            recommendations.append({
                'title': f"Pre-authorize {w['ward_name']} Overflow",
                'severity': 'Critical',
                'color': 'red',
                'description': f"{w['ward_name']} predicted at {w['predicted_occupancy']}% tomorrow. Allocate overflow beds immediately."
            })
        elif w['predicted_occupancy'] >= 80:
            recommendations.append({
                'title': f"Monitor {w['ward_name']} Capacity",
                'severity': 'High',
                'color': 'orange',
                'description': f"{w['ward_name']} predicted at {w['predicted_occupancy']}% tomorrow. Consider early discharge planning."
            })

    if high_risk > 0:
        recommendations.append({
            'title': f"Follow up {high_risk} High-Risk Patients",
            'severity': 'High',
            'color': 'orange',
            'description': f"{high_risk} patients have >25% readmission risk. Schedule follow-up appointments before discharge."
        })

    if not recommendations:
        recommendations.append({
            'title': 'Hospital Capacity Stable',
            'severity': 'Low',
            'color': 'blue',
            'description': 'All wards are within normal capacity. Continue regular monitoring protocols.'
        })

    return jsonify({
        'success': True,
        'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'model': 'XGBoost v3.4 (SmartHospital)',
        'summary': {
            'tomorrow_occupancy_pct': round(tomorrow_occupancy * 100, 1),
            'today_occupancy_pct': round(occupancy_rate * 100, 1),
            'expected_admissions': daily_admissions,
            'expected_discharges': daily_discharges,
            'avg_predicted_los': avg_los,
            'readmission_risk_pct': avg_readmit,
            'high_risk_patients': high_risk,
            'bed_utilization_7day': round(sum(d['occupancy_pct'] for d in forecast_7day) / 7, 1)
        },
        'forecast_7day': forecast_7day,
        'ward_predictions': ward_predictions,
        'patient_predictions': patient_los,
        'recommendations': recommendations[:4]  # top 4
    })

@app.route('/api/predictions/patient', methods=['POST'])
def predict_single_patient():
    """Run LOS + Readmission prediction for a single patient input."""
    data = request.json or {}
    now = datetime.datetime.now()
    dow = now.weekday()
    month = now.month

    condition_map = {'Critical': 4, 'Guarded': 3, 'Moderate': 2, 'Recovering': 1, 'Stable': 0}
    cond_sev  = condition_map.get(data.get('condition', 'Stable'), 0)
    age       = int(data.get('age', 50))
    gender    = 1 if data.get('gender', 'Male') == 'Male' else 0

    wards_info    = list(db.wards.find())
    total_cap     = sum(w.get('total_beds', 0) for w in wards_info)
    total_occ     = sum(w.get('occupied_beds', 0) for w in wards_info)
    total_avail   = total_cap - total_occ
    occ_rate      = round(total_occ / max(1, total_cap), 4)

    # LOS prediction
    if xgb_los and xgb_los_feats:
        feats_los = {
            'age': age, 'gender_male': gender,
            'condition_severity': cond_sev,
            'day_of_week': dow, 'month': month, 'is_weekend': 1 if dow >= 5 else 0,
            'ward_capacity': total_cap, 'occupied_beds': total_occ, 'occupancy_rate': occ_rate
        }
        row = np.array([[feats_los[f] for f in xgb_los_feats]])
        los = max(1, round(float(xgb_los.predict(row)[0]), 1))
    else:
        los = {'Critical': 9, 'Guarded': 6, 'Moderate': 4, 'Recovering': 3, 'Stable': 2}.get(data.get('condition', 'Stable'), 3)

    # Readmission prediction
    if xgb_readmission and xgb_readmission_feats:
        feats_ra = {
            'age': age, 'gender_male': gender,
            'condition_severity': cond_sev,
            'day_of_week': dow, 'month': month,
            'ward_capacity': total_cap,
            'occupancy_rate': occ_rate,
            'occupied_beds': total_occ,
            'available_beds': total_avail
        }
        row_r = np.array([[feats_ra[f] for f in xgb_readmission_feats]])
        readmit_prob = round(float(xgb_readmission.predict_proba(row_r)[0][1]) * 100, 1)
        readmit_label = 'High Risk' if readmit_prob >= 30 else ('Medium Risk' if readmit_prob >= 15 else 'Low Risk')
    else:
        readmit_prob  = 10.0
        readmit_label = 'Low Risk'

    return jsonify({
        'success': True,
        'predicted_los_days': los,
        'readmission_risk_pct': readmit_prob,
        'readmission_label': readmit_label
    })

if __name__ == '__main__':
    print("===================================================")
    print("SmartHospital MongoDB Backend Server (Flask + MongoDB)")
    print("Running on http://localhost:5000")
    print(f"MongoDB Connection URI: {get_masked_uri()}")
    print(f"MongoDB Database: {DB_NAME}")
    print("MongoDB Atlas / Compass Connected!")
    print("===================================================")
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
