const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, 'hospital.db');
const db = new sqlite3.Database(dbPath);

// Helper function to run query with Promises
function run(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) reject(err);
      else resolve(this);
    });
  });
}

// Helper function to get single row
function get(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => {
      if (err) reject(err);
      else resolve(row);
    });
  });
}

// Helper function to get all rows
function all(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

// Initialize Tables
async function initDb() {
  db.serialize(async () => {
    // Users table
    await run(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'Administrator',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Wards table
    await run(`
      CREATE TABLE IF NOT EXISTS wards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        total_beds INTEGER DEFAULT 0,
        occupied_beds INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Optimal',
        nurse_in_charge TEXT
      )
    `);

    // Patients table
    await run(`
      CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mrn TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        condition TEXT DEFAULT 'Stable',
        ward_id INTEGER,
        bed_id INTEGER,
        admission_date TEXT NOT NULL,
        attending_physician TEXT,
        status TEXT DEFAULT 'Admitted',
        FOREIGN KEY (ward_id) REFERENCES wards (id),
        FOREIGN KEY (bed_id) REFERENCES beds (id)
      )
    `);

    // Beds table
    await run(`
      CREATE TABLE IF NOT EXISTS beds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bed_number TEXT UNIQUE NOT NULL,
        ward_id INTEGER NOT NULL,
        bed_type TEXT NOT NULL,
        status TEXT DEFAULT 'Available',
        patient_id INTEGER,
        equipment TEXT,
        FOREIGN KEY (ward_id) REFERENCES wards (id),
        FOREIGN KEY (patient_id) REFERENCES patients (id)
      )
    `);

    // Alerts table
    await run(`
      CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        severity TEXT NOT NULL,
        category TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_resolved INTEGER DEFAULT 0
      )
    `);

    console.log('Database tables initialized successfully.');
  });
}

module.exports = {
  db,
  run,
  get,
  all,
  initDb
};
