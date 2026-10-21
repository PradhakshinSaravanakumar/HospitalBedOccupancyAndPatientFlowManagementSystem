# SmartHospital BedIQ — Hospital Bed Occupancy Management
SmartHospital BedIQ is a hospital operations dashboard designed to help staff monitor bed availability, patient admissions, ward capacity, alerts, and predictive insights. The project combines a web-based interface with backend APIs, a database, and machine-learning models.
**Note:** This is an educational/demo project. It uses synthetic training data and should not be used to make real clinical or hospital-capacity decisions without validation.

# Features
- **Bed and ward management:** View ward capacity and bed status, including occupied, available, cleaning, and maintenance states.
- **Patient management:** Track admitted and discharged patients and patient condition.
- **Dashboard KPIs:** Summarize occupancy, available capacity, critical patients, and active alerts.
- **Alerts and reports:** View operational alerts and reporting pages.
- **Machine-learning predictions (Python backend):**
  - Forecast next-day bed occupancy rate.
  - Estimate patient length of stay (LOS).
  - Predict readmission risk.
- **Seed/demo data:** Seed scripts and a generated CSV dataset support local development and demonstrations.
  
# Technology Stack
- **Frontend:** HTML, CSS, JavaScript
- **Backend options included in this repository:**
  - Python Flask API (app.py)
  - Node.js + Express API (server.js)
- **Database:** MongoDB for the Python backend (db.py); SQLite for the Node.js backend (db.js)
- **Machine learning:** Python, XGBoost, scikit-learn, pandas, NumPy, joblib
- **API support:** Flask-CORS / CORS
  
# Requirements
Install the runtime(s) for the backend you intend to use.
- Python 3.10+ recommended
- Node.js 18+ and npm (for the Express backend)
- MongoDB running locally (for the Flask backend)
- Python packages: flask, flask-cors, pymongo, numpy, pandas, scikit-learn, xgboost, joblib
Run the Python / Flask Backend
# From the project directory:
1. Create and activate a virtual environment (recommended).
2. **Install dependencies:**
   python -m venv .venv
   **Windows:**
   .venv\Scripts\activate
   **macOS/Linux:**
   source .venv/bin/activate
   
   pip install flask flask-cors pymongo numpy pandas scikit-learn xgboost joblib
3. Make sure MongoDB is running locally, or set MONGO_URI to your MongoDB connection string.
4. **Start the application:**
   python app.py
5. Open the local address printed by Flask in your browser (commonly http://127.0.0.1:5000).
The Flask backend loads saved model files from models/ when available. The training dataset is synthetic; model quality should be evaluated before any real-world use.
Run the Node.js / Express Backend
The Node.js backend uses SQLite and is an alternative API implementation. Run this backend if you want to use the Express version instead of the Flask version.
npm install
npm start
Then open http://localhost:3000.
Do not start both backends on the same port. The two backend implementations use different databases and may not have identical behavior.
Retrain the Machine-Learning Models
The repository includes a synthetic CSV dataset. To regenerate the dataset, first configure the database expected by generate_training_data.py, then run:
python generate_training_data.py
python train_model.py
The training script writes model files and feature lists into models/. Required Python packages are listed above.
# API Overview
The backend exposes REST endpoints under /api. Examples include:
- POST /api/auth/login — authenticate a demo user
- GET /api/kpis — retrieve dashboard metrics
- GET /api/wards — retrieve wards
Additional endpoints cover patients, beds, alerts, and predictions. Check app.py or server.js for the exact routes and request formats.
# Data and Security Notes
- Use only fictional/demo patient records in development.
- Do not commit real patient data, credentials, secrets, or production database files to a public repository.
- The included database and seed data may contain demonstration records.
- Authentication is intended for demonstration; review password handling, authorization, input validation, and deployment security before production use.
- Model predictions are experimental and are not medical advice.
# Future Improvements
- Add automated tests and API documentation.
- Add role-based authorization and secure password hashing.
- Add environment-based configuration and deployment instructions.
- Validate models with representative, consented, appropriately governed data.
- Add monitoring for model drift and prediction performance.
