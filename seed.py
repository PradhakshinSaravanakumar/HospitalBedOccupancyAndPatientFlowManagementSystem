from db import get_db, init_db

def seed_db():
    init_db()
    db = get_db()

    print("Seeding initial MongoDB documents into hospital_db...")

    # 1. Users Collection
    db.users.delete_many({})
    db.users.insert_one({
        "id": 1,
        "email": "admin@smarthospital.com",
        "password": "password123",
        "name": "Dr. Sarah Jenkins",
        "role": "System Administrator"
    })

    # 2. Wards Collection
    db.wards.delete_many({})
    wards_data = [
        { "id": 1, "name": "ICU Wing A", "department": "Intensive Care", "total_beds": 20, "occupied_beds": 18, "status": "Critical", "nurse_in_charge": "Nurse Alex Vance" },
        { "id": 2, "name": "Emergency Dept", "department": "Emergency", "total_beds": 35, "occupied_beds": 29, "status": "High Demand", "nurse_in_charge": "Nurse Mark Rivera" },
        { "id": 3, "name": "General Surgery", "department": "Surgery", "total_beds": 45, "occupied_beds": 32, "status": "Optimal", "nurse_in_charge": "Nurse Elena Rostova" },
        { "id": 4, "name": "Cardiology Ward", "department": "Cardiology", "total_beds": 30, "occupied_beds": 24, "status": "Optimal", "nurse_in_charge": "Nurse David Kim" },
        { "id": 5, "name": "Pediatrics Wing", "department": "Pediatrics", "total_beds": 25, "occupied_beds": 14, "status": "Optimal", "nurse_in_charge": "Nurse Rachel Green" },
        { "id": 6, "name": "Neurology Unit", "department": "Neurology", "total_beds": 15, "occupied_beds": 13, "status": "High Demand", "nurse_in_charge": "Nurse Thomas Thorne" }
    ]
    db.wards.insert_many(wards_data)

    # 3. Patients Collection
    db.patients.delete_many({})
    patients_data = [
        { "id": 1, "mrn": "MRN-884102", "name": "Eleanor Vance", "age": 64, "gender": "Female", "condition": "Critical", "ward_id": 1, "bed_id": 1, "admission_date": "2026-08-01 08:30:00", "attending_physician": "Dr. Michael Chen", "status": "Admitted" },
        { "id": 2, "mrn": "MRN-903211", "name": "Robert Miller", "age": 72, "gender": "Male", "condition": "Critical", "ward_id": 1, "bed_id": 2, "admission_date": "2026-08-02 11:15:00", "attending_physician": "Dr. Michael Chen", "status": "Admitted" },
        { "id": 3, "mrn": "MRN-441209", "name": "Sophia Martinez", "age": 45, "gender": "Female", "condition": "Stable", "ward_id": 3, "bed_id": 7, "admission_date": "2026-08-04 14:00:00", "attending_physician": "Dr. Lisa Ray", "status": "Admitted" },
        { "id": 4, "mrn": "MRN-112948", "name": "James Wilson", "age": 58, "gender": "Male", "condition": "Stable", "ward_id": 4, "bed_id": 10, "admission_date": "2026-08-05 09:45:00", "attending_physician": "Dr. Arthur Pendelton", "status": "Admitted" },
        { "id": 5, "mrn": "MRN-773012", "name": "Amira Patel", "age": 31, "gender": "Female", "condition": "Guarded", "ward_id": 2, "bed_id": 5, "admission_date": "2026-08-08 18:20:00", "attending_physician": "Dr. Marcus Vance", "status": "Admitted" },
        { "id": 6, "mrn": "MRN-665201", "name": "David Zhang", "age": 53, "gender": "Male", "condition": "Stable", "ward_id": 3, "bed_id": 8, "admission_date": "2026-08-07 10:10:00", "attending_physician": "Dr. Lisa Ray", "status": "Admitted" },
        { "id": 7, "mrn": "MRN-339102", "name": "Clara Oswald", "age": 29, "gender": "Female", "condition": "Stable", "ward_id": 5, "bed_id": 12, "admission_date": "2026-08-09 13:00:00", "attending_physician": "Dr. Susan Foreman", "status": "Admitted" },
        { "id": 8, "mrn": "MRN-551049", "name": "George Harrison", "age": 68, "gender": "Male", "condition": "Critical", "ward_id": 6, "bed_id": 13, "admission_date": "2026-08-06 16:50:00", "attending_physician": "Dr. John Watson", "status": "Admitted" }
    ]
    db.patients.insert_many(patients_data)

    # 4. Beds Collection
    db.beds.delete_many({})
    beds_data = [
        { "id": 1, "bed_number": "ICU-101", "ward_id": 1, "bed_type": "ICU Ventilator", "status": "Occupied", "patient_id": 1, "equipment": "Ventilator, Telemetry" },
        { "id": 2, "bed_number": "ICU-102", "ward_id": 1, "bed_type": "ICU Ventilator", "status": "Occupied", "patient_id": 2, "equipment": "Ventilator, Dialysis" },
        { "id": 3, "bed_number": "ICU-103", "ward_id": 1, "bed_type": "ICU Standard", "status": "Available", "patient_id": None, "equipment": "Monitor, Oxygen" },
        { "id": 4, "bed_number": "ICU-104", "ward_id": 1, "bed_type": "ICU Isolation", "status": "Maintenance", "patient_id": None, "equipment": "HEPA Filter, Negative Pressure" },
        { "id": 5, "bed_number": "EMG-201", "ward_id": 2, "bed_type": "Triage Bed", "status": "Occupied", "patient_id": 5, "equipment": "Defibrillator, Oxygen" },
        { "id": 6, "bed_number": "EMG-202", "ward_id": 2, "bed_type": "Triage Bed", "status": "Available", "patient_id": None, "equipment": "Monitor" },
        { "id": 7, "bed_number": "SURG-301", "ward_id": 3, "bed_type": "Post-Op Bed", "status": "Occupied", "patient_id": 3, "equipment": "IV Pump, Telemetry" },
        { "id": 8, "bed_number": "SURG-302", "ward_id": 3, "bed_type": "Post-Op Bed", "status": "Occupied", "patient_id": 6, "equipment": "IV Pump" },
        { "id": 9, "bed_number": "SURG-303", "ward_id": 3, "bed_type": "Post-Op Bed", "status": "Available", "patient_id": None, "equipment": "Standard" },
        { "id": 10, "bed_number": "CARD-401", "ward_id": 4, "bed_type": "Telemetry Bed", "status": "Occupied", "patient_id": 4, "equipment": "Cardiac Monitor" },
        { "id": 11, "bed_number": "CARD-402", "ward_id": 4, "bed_type": "Telemetry Bed", "status": "Available", "patient_id": None, "equipment": "Cardiac Monitor" },
        { "id": 12, "bed_number": "PED-501", "ward_id": 5, "bed_type": "Pediatric Bed", "status": "Occupied", "patient_id": 7, "equipment": "Pediatric Monitor" },
        { "id": 13, "bed_number": "NEU-601", "ward_id": 6, "bed_type": "Neurology ICU", "status": "Occupied", "patient_id": 8, "equipment": "EEG, Telemetry" }
    ]
    db.beds.insert_many(beds_data)

    # 5. Alerts Collection
    db.alerts.delete_many({})
    alerts_data = [
        { "id": 1, "title": "ICU Capacity Surge Warning", "severity": "High", "category": "Bed Capacity", "message": "ICU Wing A is currently at 90% occupancy limit (18/20 beds occupied).", "is_resolved": 0 },
        { "id": 2, "title": "Emergency Department Delay", "severity": "High", "category": "Patient Flow", "message": "Triage wait time exceeded 45 minutes for 4 non-critical patients.", "is_resolved": 0 },
        { "id": 3, "title": "Ventilator Maintenance Due", "severity": "Medium", "category": "Equipment", "message": "Bed ICU-104 negative pressure unit requires scheduled calibration.", "is_resolved": 0 },
        { "id": 4, "title": "Bed Cleaning Request", "severity": "Low", "category": "Housekeeping", "message": "Bed SURG-303 requires sanitation following patient discharge.", "is_resolved": 0 },
        { "id": 5, "title": "Pediatrics Transfer Request", "severity": "Medium", "category": "Patient Flow", "message": "Patient Clara Oswald approved for discharge prep.", "is_resolved": 0 }
    ]
    db.alerts.insert_many(alerts_data)

    print("MongoDB hospital_db seeded successfully!")

if __name__ == '__main__':
    seed_db()
