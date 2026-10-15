"""
SmartHospital - XGBoost Training Data Generator
================================================
Since real historical hospital data doesn't exist yet, this script
generates a realistic synthetic training dataset using the MongoDB
patients/wards/beds data as the base, then expands it with
statistical noise and patterns to simulate historical records.

Generated CSV: hospital_training_data.csv
"""

import random
import datetime
import pandas as pd
import numpy as np
from db import get_db

random.seed(42)
np.random.seed(42)

WARD_NAMES = ['ICU Wing A', 'Emergency Dept', 'General Surgery', 'Cardiology Ward', 'Pediatrics Wing', 'Neurology Unit']
WARD_CAPACITY = {'ICU Wing A': 20, 'Emergency Dept': 35, 'General Surgery': 45, 'Cardiology Ward': 30, 'Pediatrics Wing': 25, 'Neurology Unit': 15}
CONDITIONS = ['Critical', 'Stable', 'Guarded', 'Moderate', 'Recovering']
CONDITION_WEIGHTS = [0.12, 0.50, 0.15, 0.13, 0.10]
GENDERS = ['Male', 'Female']

def day_of_week_factor(dow):
    """Simulate weekly admission patterns (Mon/Tue high, Sun low)."""
    factors = [1.15, 1.20, 1.10, 1.05, 0.95, 0.85, 0.75]
    return factors[dow]

def generate_synthetic_data(n_records=2000):
    """Generate n_records synthetic patient records with features for ML training."""
    db = get_db()
    
    print(f"Generating {n_records} synthetic training records...")
    records = []
    start_date = datetime.datetime(2025, 1, 1)

    for i in range(n_records):
        # Random date within last 18 months
        days_offset = random.randint(0, 545)
        admission_date = start_date + datetime.timedelta(days=days_offset)
        dow = admission_date.weekday()
        month = admission_date.month
        week_of_year = admission_date.isocalendar()[1]

        # Patient demographics
        age = int(np.clip(np.random.normal(52, 20), 1, 95))
        gender = random.choice(GENDERS)
        
        # Ward and capacity
        ward_name = random.choice(WARD_NAMES)
        ward_capacity = WARD_CAPACITY[ward_name]
        
        # Occupancy influenced by day of week, month, and ward type
        base_occupancy = random.uniform(0.55, 0.98)
        occupancy_factor = day_of_week_factor(dow)
        # Winter months (Nov-Feb) have higher occupancy
        season_factor = 1.10 if month in [11, 12, 1, 2] else (0.92 if month in [6, 7, 8] else 1.0)
        occupancy_rate = min(1.0, base_occupancy * occupancy_factor * season_factor)
        occupied_beds = int(ward_capacity * occupancy_rate)
        
        # Patient condition
        condition = random.choices(CONDITIONS, weights=CONDITION_WEIGHTS)[0]
        condition_map = {'Critical': 4, 'Guarded': 3, 'Moderate': 2, 'Recovering': 1, 'Stable': 0}
        condition_severity = condition_map[condition]
        
        # Length of Stay (target for LOS prediction model)
        base_los = {'Critical': 8.5, 'Guarded': 5.5, 'Moderate': 4.0, 'Recovering': 3.0, 'Stable': 2.5}
        age_los_factor = 1 + (age - 40) * 0.015 if age > 40 else 1
        los_days = max(1, int(np.random.lognormal(np.log(base_los[condition] * age_los_factor), 0.4)))

        # Readmission risk (target for readmission classification model)
        readmit_base = {'Critical': 0.35, 'Guarded': 0.20, 'Moderate': 0.14, 'Recovering': 0.09, 'Stable': 0.06}
        age_risk = 0.003 * max(0, age - 50)
        readmission_risk = min(0.95, readmit_base[condition] + age_risk + random.uniform(-0.05, 0.05))
        will_readmit = 1 if random.random() < readmission_risk else 0

        # Tomorrow's occupancy (target for occupancy forecast model)
        next_day_occupancy = min(1.0, occupancy_rate + random.uniform(-0.06, 0.10))

        # Number of admissions today (influenced by DoW and season)
        daily_admissions = max(0, int(np.random.normal(7 * day_of_week_factor(dow) * season_factor, 2)))
        
        # Number of discharges today
        daily_discharges = max(0, int(np.random.normal(6, 2.5)))

        record = {
            # Time features
            'day_of_week': dow,
            'month': month,
            'week_of_year': week_of_year,
            'is_weekend': 1 if dow >= 5 else 0,
            'is_winter': 1 if month in [11, 12, 1, 2] else 0,
            'is_summer': 1 if month in [6, 7, 8] else 0,
            
            # Patient features
            'age': age,
            'gender_male': 1 if gender == 'Male' else 0,
            'condition_severity': condition_severity,
            
            # Ward features
            'ward_capacity': ward_capacity,
            'occupied_beds': occupied_beds,
            'available_beds': ward_capacity - occupied_beds,
            'daily_admissions': daily_admissions,
            'daily_discharges': daily_discharges,
            
            # Derived features
            'occupancy_rate': round(occupancy_rate, 4),
            'admission_discharge_ratio': round(daily_admissions / max(1, daily_discharges), 4),
            
            # TARGET VARIABLES
            'target_los_days': los_days,
            'target_readmission': will_readmit,
            'target_next_occupancy': round(next_day_occupancy, 4),
            'target_tomorrow_admissions': daily_admissions,
        }
        records.append(record)

    df = pd.DataFrame(records)
    output_path = 'hospital_training_data.csv'
    df.to_csv(output_path, index=False)
    print(f"Training dataset saved to: {output_path}")
    print(f"Shape: {df.shape}")
    print(f"\nColumn Summary:\n{df.describe().round(2).to_string()}")
    return df

if __name__ == '__main__':
    df = generate_synthetic_data(n_records=2000)
