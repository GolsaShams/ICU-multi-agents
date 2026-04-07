from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sys
import random
import math
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import text
from decimal import Decimal

OTTAWA_TZ = ZoneInfo('America/Toronto')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import get_engine, TABLE_PATIENTS, TABLE_ALERTS, TABLE_BED_AVAILABILITY, TABLE_NURSE_ASSIGNMENTS

STATIC_DIR = os.path.join(BASE_DIR, 'icu_flutter', 'build', 'web')
app = Flask(__name__)
CORS(app)

engine = None

def get_db_engine():
    global engine
    if engine is None:
        engine = get_engine()
    return engine

@app.route('/')
def serve_flutter_index():
    index_path = os.path.join(STATIC_DIR, 'index.html')
    with open(index_path, 'r', encoding='utf-8') as f:
        return f.read(), 200, {'Content-Type': 'text/html'}

@app.route('/<path:path>')
def serve_flutter_static(path):
    file_path = os.path.join(STATIC_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(STATIC_DIR, path)
    index_path = os.path.join(STATIC_DIR, 'index.html')
    with open(index_path, 'r', encoding='utf-8') as f:
        return f.read(), 200, {'Content-Type': 'text/html'}

@app.errorhandler(404)
def not_found(e):
    try:
        index_path = os.path.join(STATIC_DIR, 'index.html')
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except Exception:
        return jsonify({'error': 'Not found'}), 404

def ottawa_now():
    return datetime.now(OTTAWA_TZ).strftime('%Y-%m-%d %H:%M:%S')

def determine_status(hr, spo2, temp):
    temp = float(temp) if temp else 37.0
    if hr > 120 or spo2 < 85 or temp > 39.0:
        return 'Critical'
    if hr > 100 or spo2 < 90 or temp > 38.0:
        return 'Warning'
    return 'Stable'

def determine_rhythm(hr):
    if hr > 120:
        return random.choice(['Sinus Tachycardia', 'Atrial Fibrillation', 'Ventricular Tachycardia', 'Atrial Flutter'])
    if hr > 100:
        return random.choice(['Sinus Tachycardia', 'Atrial Flutter'])
    if hr < 55:
        return 'Sinus Bradycardia'
    return 'Normal Sinus Rhythm'

def serialize_row(row_dict):
    """Convert Decimal and datetime values to JSON-safe types."""
    d = {}
    for k, v in row_dict.items():
        if isinstance(v, Decimal):
            d[k] = float(v)
        elif isinstance(v, datetime):
            if v and v.year > 1:
                d[k] = v.strftime('%Y-%m-%d %H:%M:%S')
            else:
                d[k] = None
        else:
            d[k] = v
    return d

def adapt_patient(p):
    """Map Navid's 'rhythm' column to Flutter's expected 'heart_rhythm'."""
    d = serialize_row(p)
    d['heart_rhythm'] = d.pop('rhythm', d.get('heart_rhythm', 'Normal Sinus Rhythm'))
    return d

def adapt_bed(b):
    """Add 'is_occupied' field derived from status for Flutter compatibility."""
    d = serialize_row(b)
    d['is_occupied'] = 1 if d.get('status') == 'Occupied' else 0
    d.setdefault('last_updated', d.get('admission_date'))
    return d

def adapt_nurse(n):
    """Add 'last_updated' field for Flutter compatibility."""
    d = serialize_row(n)
    d.setdefault('last_updated', ottawa_now())
    return d

# ── Background simulation thread ──

def simulate_vitals():
    while True:
        time.sleep(5)
        try:
            eng = get_db_engine()
            with eng.begin() as conn:
                result = conn.execute(text(f'SELECT * FROM {TABLE_PATIENTS}'))
                patients = [dict(row) for row in result.mappings().all()]

                for p in patients:
                    hr_delta = random.choice([d for d in range(-5, 6) if d != 0])
                    spo2_delta = random.choice([d for d in range(-2, 3) if d != 0])
                    temp_delta = random.choice([-0.3, -0.2, -0.1, 0.1, 0.2, 0.3])

                    new_hr = max(40, min(160, (p['hr'] or 80) + hr_delta))
                    new_spo2 = max(70, min(100, (p['spo2'] or 95) + spo2_delta))
                    old_temp = float(p['temp']) if p['temp'] else 37.0
                    new_temp = round(max(35.0, min(41.0, old_temp + temp_delta)), 1)
                    new_status = determine_status(new_hr, new_spo2, new_temp)
                    new_rhythm = determine_rhythm(new_hr)

                    conn.execute(
                        text(f'UPDATE {TABLE_PATIENTS} SET hr=:hr, spo2=:spo2, temp=:temp, rhythm=:rhythm, status=:status, last_updated=:lu WHERE bed_id=:bed'),
                        {'hr': new_hr, 'spo2': new_spo2, 'temp': new_temp, 'rhythm': new_rhythm, 'status': new_status, 'lu': ottawa_now(), 'bed': p['bed_id']}
                    )

                    old_status = p['status']
                    if new_status == 'Critical' and old_status != 'Critical':
                        msg = f"ALERT: {p['bed_id']} deteriorated to CRITICAL (HR={new_hr}, SpO2={new_spo2}, Temp={new_temp} C)"
                        conn.execute(
                            text(f'INSERT INTO {TABLE_ALERTS} (bed_id, message, timestamp) VALUES (:bed, :msg, :ts)'),
                            {'bed': p['bed_id'], 'msg': msg, 'ts': ottawa_now()}
                        )

                now = ottawa_now()
                updated = conn.execute(text(f'SELECT bed_id, status FROM {TABLE_PATIENTS}')).mappings().all()
                critical_beds = {r['bed_id'] for r in updated if r['status'] == 'Critical'}
                warning_beds = {r['bed_id'] for r in updated if r['status'] == 'Warning'}

                nurses = conn.execute(text(f'SELECT * FROM {TABLE_NURSE_ASSIGNMENTS}')).mappings().all()
                for n in nurses:
                    assigned = n['assigned_beds'] or ''
                    beds = [b.strip() for b in assigned.split(',') if b.strip()]
                    critical_count = sum(1 for b in beds if b in critical_beds)
                    warning_count = sum(1 for b in beds if b in warning_beds)

                    if critical_count >= 2 or len(beds) >= 3:
                        workload = 'Overloaded'
                    elif critical_count >= 1 or warning_count >= 2:
                        workload = 'High'
                    else:
                        workload = 'Normal'

                    conn.execute(
                        text(f'UPDATE {TABLE_NURSE_ASSIGNMENTS} SET workload=:wl WHERE nurse_id=:nid'),
                        {'wl': workload, 'nid': n['nurse_id']}
                    )

                    if workload == 'Overloaded' and n['workload'] != 'Overloaded':
                        msg = f"Nurse Agent: {n['nurse_name']} is OVERLOADED with {critical_count} critical patient(s) - requesting backup!"
                        conn.execute(
                            text(f'INSERT INTO {TABLE_ALERTS} (bed_id, message, timestamp) VALUES (:bed, :msg, :ts)'),
                            {'bed': beds[0] if beds else 'unknown', 'msg': msg, 'ts': now}
                        )

        except Exception as e:
            print(f"Simulation error: {e}")

# ── ECG waveform generator ──

def generate_ecg_waveform(hr, rhythm, num_points=200):
    points = []
    beats_per_sec = hr / 60.0
    duration = 4.0
    for i in range(num_points):
        t = (i / num_points) * duration
        phase = (t * beats_per_sec) % 1.0
        y = 0.0
        if 0.0 <= phase < 0.05:
            y = 0.15 * math.sin(math.pi * phase / 0.05)
        elif 0.08 <= phase < 0.10:
            y = -0.1 * math.sin(math.pi * (phase - 0.08) / 0.02)
        elif 0.10 <= phase < 0.16:
            y = 1.0 * math.sin(math.pi * (phase - 0.10) / 0.06)
        elif 0.16 <= phase < 0.20:
            y = -0.25 * math.sin(math.pi * (phase - 0.16) / 0.04)
        elif 0.28 <= phase < 0.40:
            y = 0.25 * math.sin(math.pi * (phase - 0.28) / 0.12)
        if 'Fibrillation' in (rhythm or ''):
            y += random.uniform(-0.08, 0.08)
        else:
            y += random.uniform(-0.02, 0.02)
        points.append(round(y, 4))
    return points

# ── API routes ──

@app.route('/view', methods=['GET'])
def view():
    eng = get_db_engine()
    with eng.connect() as conn:
        patients = [adapt_patient(dict(r)) for r in conn.execute(text(f'SELECT * FROM {TABLE_PATIENTS}')).mappings().all()]
        alerts = [serialize_row(dict(r)) for r in conn.execute(text(f'SELECT * FROM {TABLE_ALERTS} ORDER BY timestamp DESC LIMIT 20')).mappings().all()]
        beds = [adapt_bed(dict(r)) for r in conn.execute(text(f'SELECT * FROM {TABLE_BED_AVAILABILITY} ORDER BY bed_id')).mappings().all()]
        nurses = [adapt_nurse(dict(r)) for r in conn.execute(text(f'SELECT * FROM {TABLE_NURSE_ASSIGNMENTS} ORDER BY nurse_id')).mappings().all()]
    return jsonify({'patients': patients, 'alerts': alerts, 'beds': beds, 'nurses': nurses, 'server_time': ottawa_now()})

@app.route('/patient/<bed_id>', methods=['GET'])
def patient_detail(bed_id):
    eng = get_db_engine()
    with eng.connect() as conn:
        result = conn.execute(text(f'SELECT * FROM {TABLE_PATIENTS} WHERE bed_id=:bed'), {'bed': bed_id}).mappings().all()
        if not result:
            return jsonify({'error': 'Patient not found'}), 404
        p = adapt_patient(dict(result[0]))
        alerts = [serialize_row(dict(r)) for r in conn.execute(text(f'SELECT * FROM {TABLE_ALERTS} WHERE bed_id=:bed ORDER BY timestamp DESC LIMIT 50'), {'bed': bed_id}).mappings().all()]
    ecg = generate_ecg_waveform(p['hr'], p.get('heart_rhythm', ''))
    return jsonify({'patient': p, 'alerts': alerts, 'ecg': ecg, 'server_time': ottawa_now()})

@app.route('/beds', methods=['GET'])
def beds_view():
    eng = get_db_engine()
    with eng.connect() as conn:
        beds = [adapt_bed(dict(r)) for r in conn.execute(text(f'SELECT * FROM {TABLE_BED_AVAILABILITY} ORDER BY bed_id')).mappings().all()]
    occupied = sum(1 for b in beds if b['is_occupied'])
    total = len(beds)
    return jsonify({'beds': beds, 'total': total, 'occupied': occupied, 'available': total - occupied,
        'occupancy_rate': round((occupied / total) * 100, 1) if total else 0, 'server_time': ottawa_now()})

@app.route('/nurses', methods=['GET'])
def nurses_view():
    eng = get_db_engine()
    with eng.connect() as conn:
        nurses = [adapt_nurse(dict(r)) for r in conn.execute(text(f'SELECT * FROM {TABLE_NURSE_ASSIGNMENTS} ORDER BY nurse_id')).mappings().all()]
    overloaded = sum(1 for n in nurses if n['workload'] == 'Overloaded')
    high = sum(1 for n in nurses if n['workload'] == 'High')
    return jsonify({'nurses': nurses, 'total': len(nurses), 'overloaded': overloaded, 'high_workload': high,
        'normal': len(nurses) - overloaded - high, 'server_time': ottawa_now()})

@app.route('/post_alert', methods=['POST'])
def post_alert():
    data = request.json
    eng = get_db_engine()
    with eng.begin() as conn:
        conn.execute(
            text(f'INSERT INTO {TABLE_ALERTS} (bed_id, message, timestamp) VALUES (:bed, :msg, :ts)'),
            {'bed': data['bed_id'], 'msg': data['alert'], 'ts': ottawa_now()}
        )
    return jsonify({'status': 'success'})

# ── Start simulation ──

sim_thread = threading.Thread(target=simulate_vitals, daemon=True)
sim_thread.start()
print("[OK] Real-time vitals simulation started (updates every 5s)")

if __name__ == "__main__":
    app.run(debug=False, port=5000)
