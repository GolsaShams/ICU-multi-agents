import os
import sqlite3
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "icu_agents.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS patients')
    cursor.execute('DROP TABLE IF EXISTS alerts')
    cursor.execute('DROP TABLE IF EXISTS bed_availability')
    cursor.execute('DROP TABLE IF EXISTS nurse_assignments')
    
    # Create unified patients table
    cursor.execute('''
        CREATE TABLE patients (
            bed_id TEXT PRIMARY KEY,
            hr INTEGER,
            spo2 INTEGER,
            temp REAL,
            heart_rhythm TEXT,
            status TEXT
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bed_id TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create bed availability table
    cursor.execute('''
        CREATE TABLE bed_availability (
            bed_id TEXT PRIMARY KEY,
            is_occupied INTEGER DEFAULT 0,
            patient_name TEXT,
            admission_date DATETIME,
            expected_discharge DATETIME,
            status TEXT DEFAULT 'Available',
            last_updated DATETIME
        )
    ''')
    
    # Create nurse assignments table
    cursor.execute('''
        CREATE TABLE nurse_assignments (
            nurse_id TEXT PRIMARY KEY,
            nurse_name TEXT,
            assigned_beds TEXT,
            shift TEXT,
            workload TEXT DEFAULT 'Normal',
            last_updated DATETIME
        )
    ''')
    
    # Patient vitals samples
    patients_samples = [
        ('bed_01', 115, 87, 39.1, 'Sinus Tachycardia', 'Critical'),
        ('bed_02', 72, 98, 36.6, 'Normal Sinus Rhythm', 'Stable'),
        ('bed_03', 88, 84, 37.0, 'Normal Sinus Rhythm', 'Warning'),
        ('bed_04', 120, 95, 38.8, 'Atrial Fibrillation', 'Critical'),
        ('bed_05', 65, 97, 36.8, 'Normal Sinus Rhythm', 'Stable'),
        ('bed_06', 102, 91, 37.9, 'Sinus Tachycardia', 'Warning'),
        ('bed_08', 130, 82, 39.5, 'Ventricular Tachycardia', 'Critical'),
        ('bed_09', 90, 96, 37.2, 'Normal Sinus Rhythm', 'Stable'),
        ('bed_10', 110, 88, 38.4, 'Atrial Flutter', 'Critical'),
    ]
    cursor.executemany('INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?)', patients_samples)
    
    # Bed availability samples (synced with patients)
    now = datetime.now().isoformat()
    patient_names = [
        'John Smith', 'Maria Garcia', 'David Lee', 'Sarah Johnson',
        'Ahmed Hassan', 'Emily Brown', None, 'Robert Chen',
        'Lisa Wang', 'James Wilson'
    ]
    # Expected days until discharge for each bed (None for unoccupied)
    discharge_days = [2, 5, 1, 3, 7, 4, None, 1, 6, 2]
    bed_samples = []
    for i in range(1, 11):
        bed_id = f'bed_{i:02d}'
        name = patient_names[i - 1]
        is_occupied = 1 if name else 0
        admission = (datetime.now() - timedelta(days=i, hours=i*3)).isoformat() if is_occupied else None
        days_left = discharge_days[i - 1]
        discharge = (datetime.now() + timedelta(days=days_left, hours=i*2)).isoformat() if (is_occupied and days_left) else None
        status = 'Occupied' if is_occupied else 'Available'
        bed_samples.append((bed_id, is_occupied, name, admission, discharge, status, now))
    cursor.executemany('INSERT INTO bed_availability VALUES (?, ?, ?, ?, ?, ?, ?)', bed_samples)
    
    # Nurse assignment samples
    nurse_samples = [
        ('nurse_01', 'Alice Thompson', 'bed_01,bed_02', 'Day (07:00-19:00)', 'High', now),
        ('nurse_02', 'Bob Martinez', 'bed_03,bed_04', 'Day (07:00-19:00)', 'High', now),
        ('nurse_03', 'Carol White', 'bed_05,bed_06', 'Day (07:00-19:00)', 'Normal', now),
        ('nurse_04', 'Daniel Kim', 'bed_07,bed_08', 'Night (19:00-07:00)', 'High', now),
        ('nurse_05', 'Eva Nguyen', 'bed_09,bed_10', 'Night (19:00-07:00)', 'High', now),
    ]
    cursor.executemany('INSERT INTO nurse_assignments VALUES (?, ?, ?, ?, ?, ?)', nurse_samples)
    
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' initialized successfully.")

if __name__ == "__main__":
    init_db()