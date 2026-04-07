import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import get_engine, TABLE_PATIENTS, TABLE_ALERTS, TABLE_BED_AVAILABILITY, TABLE_NURSE_ASSIGNMENTS

def init_db():
    engine = get_engine()

    # Insert sample data only if tables are empty
    with engine.begin() as conn:
        count = conn.execute(text(f'SELECT COUNT(*) FROM {TABLE_PATIENTS}')).scalar()
        if count == 0:
            patients_samples = [
                ('bed_01', 115, 87, 39.1, 'Critical', 'Sinus Tachycardia'),
                ('bed_02', 72, 98, 36.6, 'Stable', 'Normal Sinus Rhythm'),
                ('bed_03', 88, 84, 37.0, 'Warning', 'Normal Sinus Rhythm'),
                ('bed_04', 120, 95, 38.8, 'Critical', 'Atrial Fibrillation'),
                ('bed_05', 65, 97, 36.8, 'Stable', 'Normal Sinus Rhythm'),
                ('bed_06', 102, 91, 37.9, 'Warning', 'Sinus Tachycardia'),
                ('bed_08', 130, 82, 39.5, 'Critical', 'Ventricular Tachycardia'),
                ('bed_09', 90, 96, 37.2, 'Stable', 'Normal Sinus Rhythm'),
                ('bed_10', 110, 88, 38.4, 'Critical', 'Atrial Flutter'),
            ]
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for p in patients_samples:
                conn.execute(
                    text(f'INSERT INTO {TABLE_PATIENTS} (bed_id, hr, spo2, temp, status, rhythm, last_updated) VALUES (:b, :h, :s, :t, :st, :r, :lu)'),
                    {'b': p[0], 'h': p[1], 's': p[2], 't': p[3], 'st': p[4], 'r': p[5], 'lu': now}
                )

        count = conn.execute(text(f'SELECT COUNT(*) FROM {TABLE_BED_AVAILABILITY}')).scalar()
        if count == 0:
            patient_names = ['John Smith', 'Maria Garcia', 'David Lee', 'Sarah Johnson',
                'Ahmed Hassan', 'Emily Brown', None, 'Robert Chen', 'Lisa Wang', 'James Wilson']
            discharge_days = [2, 5, 1, 3, 7, 4, None, 1, 6, 2]
            for i in range(1, 11):
                bed_id = f'bed_{i:02d}'
                name = patient_names[i - 1]
                is_occupied = True if name else False
                admission = (datetime.now() - timedelta(days=i, hours=i*3)).strftime('%Y-%m-%d %H:%M:%S') if is_occupied else None
                days_left = discharge_days[i - 1]
                discharge = (datetime.now() + timedelta(days=days_left, hours=i*2)).strftime('%Y-%m-%d %H:%M:%S') if (is_occupied and days_left) else None
                status = 'Occupied' if is_occupied else 'Available'
                conn.execute(
                    text(f'INSERT INTO {TABLE_BED_AVAILABILITY} (bed_id, status, patient_name, admission_date, expected_discharge) VALUES (:a, :b, :c, :d, :e)'),
                    {'a': bed_id, 'b': status, 'c': name, 'd': admission, 'e': discharge}
                )

        count = conn.execute(text(f'SELECT COUNT(*) FROM {TABLE_NURSE_ASSIGNMENTS}')).scalar()
        if count == 0:
            nurse_samples = [
                ('nurse_01', 'Alice Thompson', 'Day', 'bed_01,bed_02', 'High'),
                ('nurse_02', 'Bob Martinez', 'Day', 'bed_03,bed_04', 'High'),
                ('nurse_03', 'Carol White', 'Day', 'bed_05,bed_06', 'Normal'),
                ('nurse_04', 'Daniel Kim', 'Night', 'bed_07,bed_08', 'High'),
                ('nurse_05', 'Eva Nguyen', 'Night', 'bed_09,bed_10', 'High'),
            ]
            for n in nurse_samples:
                conn.execute(
                    text(f'INSERT INTO {TABLE_NURSE_ASSIGNMENTS} (nurse_id, nurse_name, shift, assigned_beds, workload) VALUES (:a, :b, :c, :d, :e)'),
                    {'a': n[0], 'b': n[1], 'c': n[2], 'd': n[3], 'e': n[4]}
                )

    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
