"""
Sync and expand beds in MongoDB to guarantee real 1:1 patient-to-bed relationships.
"""
from db import get_db

def sync():
    db = get_db()
    wards = {w['id']: w for w in db.wards.find()}

    # Update patients 1-8
    for b in db.beds.find():
        if b.get('patient_id'):
            w = wards.get(b.get('ward_id'), {})
            db.patients.update_one(
                {'id': b['patient_id']},
                {'$set': {
                    'bed_id': b['id'],
                    'bed_number': b['bed_number'],
                    'ward_id': b.get('ward_id'),
                    'ward_name': w.get('name', 'General')
                }}
            )

    # Assign bed 9 to patient 9
    db.beds.update_one({'id': 9}, {'$set': {'status': 'Occupied', 'patient_id': 9}})
    db.patients.update_one(
        {'id': 9},
        {'$set': {
            'bed_id': 9,
            'bed_number': 'SURG-303',
            'ward_id': 3,
            'ward_name': 'General Surgery'
        }}
    )

    # Extra beds to cover patients 10, 11, 12 and provide Available + Cleaning beds
    extra_beds = [
        {'id': 14, 'bed_number': 'CARD-403', 'ward_id': 4, 'bed_type': 'Telemetry Bed', 'status': 'Occupied', 'patient_id': 10, 'equipment': 'Cardiac Monitor'},
        {'id': 15, 'bed_number': 'NEU-602', 'ward_id': 6, 'bed_type': 'Neurology ICU', 'status': 'Occupied', 'patient_id': 11, 'equipment': 'EEG Monitor'},
        {'id': 16, 'bed_number': 'ICU-105', 'ward_id': 1, 'bed_type': 'ICU Ventilator', 'status': 'Occupied', 'patient_id': 12, 'equipment': 'Ventilator'},
        {'id': 17, 'bed_number': 'ORTH-701', 'ward_id': 7, 'bed_type': 'Post-Op Bed', 'status': 'Available', 'patient_id': None, 'equipment': 'Standard'},
        {'id': 18, 'bed_number': 'ORTH-702', 'ward_id': 7, 'bed_type': 'Traction Bed', 'status': 'Cleaning', 'patient_id': None, 'equipment': 'Traction Frame'},
        {'id': 19, 'bed_number': 'MAT-801', 'ward_id': 8, 'bed_type': 'Birthing Suite', 'status': 'Available', 'patient_id': None, 'equipment': 'Infant Monitor'},
        {'id': 20, 'bed_number': 'MAT-802', 'ward_id': 8, 'bed_type': 'Postpartum Bed', 'status': 'Cleaning', 'patient_id': None, 'equipment': 'Standard'},
        {'id': 21, 'bed_number': 'ICU-106', 'ward_id': 1, 'bed_type': 'ICU Standard', 'status': 'Available', 'patient_id': None, 'equipment': 'Monitor'},
        {'id': 22, 'bed_number': 'EMG-203', 'ward_id': 2, 'bed_type': 'Triage Bed', 'status': 'Cleaning', 'patient_id': None, 'equipment': 'Defibrillator'}
    ]

    for b in extra_beds:
        db.beds.update_one({'id': b['id']}, {'$set': b}, upsert=True)

    db.patients.update_one({'id': 10}, {'$set': {'bed_id': 14, 'bed_number': 'CARD-403', 'ward_id': 4, 'ward_name': 'Cardiology Ward'}})
    db.patients.update_one({'id': 11}, {'$set': {'bed_id': 15, 'bed_number': 'NEU-602', 'ward_id': 6, 'ward_name': 'Neurology Unit'}})
    db.patients.update_one({'id': 12}, {'$set': {'bed_id': 16, 'bed_number': 'ICU-105', 'ward_id': 1, 'ward_name': 'ICU Wing A'}})

    total_beds = db.beds.count_documents({})
    occupied = db.beds.count_documents({'status': 'Occupied'})
    cleaning = db.beds.count_documents({'status': 'Cleaning'})
    available = db.beds.count_documents({'status': 'Available'})
    admitted = db.patients.count_documents({'status': 'Admitted'})

    print(f"Beds sync successful!")
    print(f"Total Beds: {total_beds}")
    print(f"Occupied Beds: {occupied} (Matches Admitted Patients: {admitted})")
    print(f"Available Beds: {available}")
    print(f"Cleaning Beds: {cleaning}")

if __name__ == '__main__':
    sync()
