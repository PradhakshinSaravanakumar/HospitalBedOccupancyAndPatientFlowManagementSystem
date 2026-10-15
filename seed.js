const { db, run, get, all, initDb } = require('./db');

async function seed() {
  await initDb();

  // Wait 500ms for table creation to finish
  await new Promise(res => setTimeout(res, 500));

  console.log('Seeding initial hospital database records...');

  try {
    // 1. Seed Admin User
    await run(`INSERT OR IGNORE INTO users (id, email, password, name, role) VALUES 
      (1, 'admin@smarthospital.com', 'password123', 'Dr. Sarah Jenkins', 'System Administrator')`);

    // 2. Clear existing records to ensure clean seed
    await run(`DELETE FROM alerts`);
    await run(`DELETE FROM patients`);
    await run(`DELETE FROM beds`);
    await run(`DELETE FROM wards`);

    // 3. Seed Wards
    const wardsData = [
      { id: 1, name: 'ICU Wing A', department: 'Intensive Care', total_beds: 20, occupied_beds: 18, status: 'Critical', nurse: 'Nurse Alex Vance' },
      { id: 2, name: 'Emergency Dept', department: 'Emergency', total_beds: 35, occupied_beds: 29, status: 'High Demand', nurse: 'Nurse Mark Rivera' },
      { id: 3, name: 'General Surgery', department: 'Surgery', total_beds: 45, occupied_beds: 32, status: 'Optimal', nurse: 'Nurse Elena Rostova' },
      { id: 4, name: 'Cardiology Ward', department: 'Cardiology', total_beds: 30, occupied_beds: 24, status: 'Optimal', nurse: 'Nurse David Kim' },
      { id: 5, name: 'Pediatrics Wing', department: 'Pediatrics', total_beds: 25, occupied_beds: 14, status: 'Optimal', nurse: 'Nurse Rachel Green' },
      { id: 6, name: 'Neurology Unit', department: 'Neurology', total_beds: 15, occupied_beds: 13, status: 'High Demand', nurse: 'Nurse Thomas Thorne' }
    ];

    for (const w of wardsData) {
      await run(
        `INSERT INTO wards (id, name, department, total_beds, occupied_beds, status, nurse_in_charge) VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [w.id, w.name, w.department, w.total_beds, w.occupied_beds, w.status, w.nurse]
      );
    }

    // 4. Seed Patients
    const patientsData = [
      { id: 1, mrn: 'MRN-884102', name: 'Eleanor Vance', age: 64, gender: 'Female', condition: 'Critical', ward_id: 1, admission_date: '2026-08-01 08:30:00', physician: 'Dr. Michael Chen', status: 'Admitted' },
      { id: 2, mrn: 'MRN-903211', name: 'Robert Miller', age: 72, gender: 'Male', condition: 'Critical', ward_id: 1, admission_date: '2026-08-02 11:15:00', physician: 'Dr. Michael Chen', status: 'Admitted' },
      { id: 3, mrn: 'MRN-441209', name: 'Sophia Martinez', age: 45, gender: 'Female', condition: 'Stable', ward_id: 3, admission_date: '2026-08-04 14:00:00', physician: 'Dr. Lisa Ray', status: 'Admitted' },
      { id: 4, mrn: 'MRN-112948', name: 'James Wilson', age: 58, gender: 'Male', condition: 'Stable', ward_id: 4, admission_date: '2026-08-05 09:45:00', physician: 'Dr. Arthur Pendelton', status: 'Admitted' },
      { id: 5, mrn: 'MRN-773012', name: 'Amira Patel', age: 31, gender: 'Female', condition: 'Guarded', ward_id: 2, admission_date: '2026-08-08 18:20:00', physician: 'Dr. Marcus Vance', status: 'Admitted' },
      { id: 6, mrn: 'MRN-665201', name: 'David Zhang', age: 53, gender: 'Male', condition: 'Stable', ward_id: 3, admission_date: '2026-08-07 10:10:00', physician: 'Dr. Lisa Ray', status: 'Admitted' },
      { id: 7, mrn: 'MRN-339102', name: 'Clara Oswald', age: 29, gender: 'Female', condition: 'Stable', ward_id: 5, admission_date: '2026-08-09 13:00:00', physician: 'Dr. Susan Foreman', status: 'Admitted' },
      { id: 8, mrn: 'MRN-551049', name: 'George Harrison', age: 68, gender: 'Male', condition: 'Critical', ward_id: 6, admission_date: '2026-08-06 16:50:00', physician: 'Dr. John Watson', status: 'Admitted' }
    ];

    for (const p of patientsData) {
      await run(
        `INSERT INTO patients (id, mrn, name, age, gender, condition, ward_id, admission_date, attending_physician, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [p.id, p.mrn, p.name, p.age, p.gender, p.condition, p.ward_id, p.admission_date, p.physician, p.status]
      );
    }

    // 5. Seed Beds
    const bedsData = [
      { bed_number: 'ICU-101', ward_id: 1, bed_type: 'ICU Ventilator', status: 'Occupied', patient_id: 1, equipment: 'Ventilator, Telemetry' },
      { bed_number: 'ICU-102', ward_id: 1, bed_type: 'ICU Ventilator', status: 'Occupied', patient_id: 2, equipment: 'Ventilator, Dialysis' },
      { bed_number: 'ICU-103', ward_id: 1, bed_type: 'ICU Standard', status: 'Available', patient_id: null, equipment: 'Monitor, Oxygen' },
      { bed_number: 'ICU-104', ward_id: 1, bed_type: 'ICU Isolation', status: 'Maintenance', patient_id: null, equipment: 'HEPA Filter, Negative Pressure' },
      { bed_number: 'EMG-201', ward_id: 2, bed_type: 'Triage Bed', status: 'Occupied', patient_id: 5, equipment: 'Defibrillator, Oxygen' },
      { bed_number: 'EMG-202', ward_id: 2, bed_type: 'Triage Bed', status: 'Available', patient_id: null, equipment: 'Monitor' },
      { bed_number: 'SURG-301', ward_id: 3, bed_type: 'Post-Op Bed', status: 'Occupied', patient_id: 3, equipment: 'IV Pump, Telemetry' },
      { bed_number: 'SURG-302', ward_id: 3, bed_type: 'Post-Op Bed', status: 'Occupied', patient_id: 6, equipment: 'IV Pump' },
      { bed_number: 'SURG-303', ward_id: 3, bed_type: 'Post-Op Bed', status: 'Available', patient_id: null, equipment: 'Standard' },
      { bed_number: 'CARD-401', ward_id: 4, bed_type: 'Telemetry Bed', status: 'Occupied', patient_id: 4, equipment: 'Cardiac Monitor' },
      { bed_number: 'CARD-402', ward_id: 4, bed_type: 'Telemetry Bed', status: 'Available', patient_id: null, equipment: 'Cardiac Monitor' },
      { bed_number: 'PED-501', ward_id: 5, bed_type: 'Pediatric Bed', status: 'Occupied', patient_id: 7, equipment: 'Pediatric Monitor' },
      { bed_number: 'NEU-601', ward_id: 6, bed_type: 'Neurology ICU', status: 'Occupied', patient_id: 8, equipment: 'EEG, Telemetry' }
    ];

    for (const b of bedsData) {
      await run(
        `INSERT INTO beds (bed_number, ward_id, bed_type, status, patient_id, equipment) VALUES (?, ?, ?, ?, ?, ?)`,
        [b.bed_number, b.ward_id, b.bed_type, b.status, b.patient_id, b.equipment]
      );
    }

    // Link bed_id back to patients
    for (const b of bedsData) {
      if (b.patient_id) {
        const bedRow = await get(`SELECT id FROM beds WHERE bed_number = ?`, [b.bed_number]);
        if (bedRow) {
          await run(`UPDATE patients SET bed_id = ? WHERE id = ?`, [bedRow.id, b.patient_id]);
        }
      }
    }

    // 6. Seed Alerts
    const alertsData = [
      { title: 'ICU Capacity Surge Warning', severity: 'High', category: 'Bed Capacity', message: 'ICU Wing A is currently at 90% occupancy limit (18/20 beds occupied).' },
      { title: 'Emergency Department Delay', severity: 'High', category: 'Patient Flow', message: 'Triage wait time exceeded 45 minutes for 4 non-critical patients.' },
      { title: 'Ventilator Maintenance Due', severity: 'Medium', category: 'Equipment', message: 'Bed ICU-104 negative pressure unit requires scheduled calibration.' },
      { title: 'Bed Cleaning Request', severity: 'Low', category: 'Housekeeping', message: 'Bed SURG-303 requires sanitation following patient discharge.' },
      { title: 'Pediatrics Transfer Request', severity: 'Medium', category: 'Patient Flow', message: 'Patient Clara Oswald approved for discharge prep.' }
    ];

    for (const a of alertsData) {
      await run(
        `INSERT INTO alerts (title, severity, category, message) VALUES (?, ?, ?, ?)`,
        [a.title, a.severity, a.category, a.message]
      );
    }

    console.log('Database seeded successfully!');
  } catch (err) {
    console.error('Error seeding database:', err);
  }
}

if (require.main === module) {
  seed().then(() => process.exit(0));
}

module.exports = seed;
