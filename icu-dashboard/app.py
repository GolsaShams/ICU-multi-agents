from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import sqlite3
import random
import math
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
# Ottawa timezone
OTTAWA_TZ = ZoneInfo('America/Toronto')

# Ensure we import init_db and DB_NAME from the project root,
# so both the initializer and API use the exact same SQLite file.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from init_db import DB_NAME, init_db  # noqa: E402

# Configure Flask to serve the built Flutter web app
STATIC_DIR = os.path.join(BASE_DIR, 'icu_flutter', 'build', 'web')
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='')
CORS(app)

@app.route('/')
def serve_flutter_index():
    return app.send_static_file('index.html')

@app.errorhandler(404)
def not_found(e):
    # For single-page apps (Flutter web), route everything to index.html
    return app.send_static_file('index.html')


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def ottawa_now():
    """Return current Ottawa time as a formatted string."""
    return datetime.now(OTTAWA_TZ).strftime('%Y-%m-%d %H:%M:%S')


def determine_status(hr, spo2, temp):
    """Auto-determine patient status from vitals."""
    if hr > 120 or spo2 < 85 or temp > 39.0:
        return 'Critical'
    if hr > 100 or spo2 < 90 or temp > 38.0:
        return 'Warning'
    return 'Stable'


def determine_rhythm(hr):
    """Pick a plausible heart rhythm label based on HR."""
    if hr > 120:
        return random.choice(['Sinus Tachycardia', 'Atrial Fibrillation',
                              'Ventricular Tachycardia', 'Atrial Flutter'])
    if hr > 100:
        return random.choice(['Sinus Tachycardia', 'Atrial Flutter'])
    if hr < 55:
        return 'Sinus Bradycardia'
    return 'Normal Sinus Rhythm'


# ── Background simulation thread ────────────────────────────────────────

def simulate_vitals():
    """Every 5 seconds, randomly adjust each patient's vitals and update bed/nurse data."""
    while True:
        time.sleep(5)
        try:
            conn = sqlite3.connect(DB_NAME)
            conn.row_factory = sqlite3.Row
            patients = conn.execute('SELECT * FROM patients').fetchall()

            for p in patients:
                # Always produce a non-zero change
                hr_delta = random.choice([d for d in range(-5, 6) if d != 0])
                spo2_delta = random.choice([d for d in range(-2, 3) if d != 0])
                temp_delta = random.choice([-0.3, -0.2, -0.1, 0.1, 0.2, 0.3])

                new_hr   = max(40, min(160, p['hr']   + hr_delta))
                new_spo2 = max(70, min(100, p['spo2'] + spo2_delta))
                new_temp = round(max(35.0, min(41.0, p['temp'] + temp_delta)), 1)

                new_status = determine_status(new_hr, new_spo2, new_temp)
                new_rhythm = determine_rhythm(new_hr)

                conn.execute(
                    '''UPDATE patients
                       SET hr = ?, spo2 = ?, temp = ?,
                           heart_rhythm = ?, status = ?
                       WHERE bed_id = ?''',
                    (new_hr, new_spo2, new_temp, new_rhythm, new_status, p['bed_id']),
                )

                # Auto-generate alert when status worsens to Critical
                old_status = p['status']
                if new_status == 'Critical' and old_status != 'Critical':
                    msg = (f"ALERT: {p['bed_id']} deteriorated to CRITICAL "
                           f"(HR={new_hr}, SpO2={new_spo2}, Temp={new_temp}°C)")
                    conn.execute(
                        'INSERT INTO alerts (bed_id, message, timestamp) VALUES (?, ?, ?)',
                        (p['bed_id'], msg, ottawa_now()),
                    )

            # ── Update nurse workloads based on current patient statuses ──
            now = ottawa_now()
            updated_patients = conn.execute('SELECT bed_id, status FROM patients').fetchall()
            critical_beds = {r['bed_id'] for r in updated_patients if r['status'] == 'Critical'}
            warning_beds = {r['bed_id'] for r in updated_patients if r['status'] == 'Warning'}

            nurses = conn.execute('SELECT * FROM nurse_assignments').fetchall()
            for n in nurses:
                beds = [b.strip() for b in n['assigned_beds'].split(',') if b.strip()]
                critical_count = sum(1 for b in beds if b in critical_beds)
                warning_count = sum(1 for b in beds if b in warning_beds)

                if critical_count >= 2 or len(beds) >= 3:
                    workload = 'Overloaded'
                elif critical_count >= 1 or warning_count >= 2:
                    workload = 'High'
                else:
                    workload = 'Normal'

                conn.execute(
                    'UPDATE nurse_assignments SET workload = ?, last_updated = ? WHERE nurse_id = ?',
                    (workload, now, n['nurse_id']),
                )

                # Alert if a nurse becomes overloaded
                if workload == 'Overloaded' and n['workload'] != 'Overloaded':
                    msg = (f"Nurse Agent: {n['nurse_name']} is OVERLOADED with "
                           f"{critical_count} critical patient(s) — requesting backup!")
                    conn.execute(
                        'INSERT INTO alerts (bed_id, message, timestamp) VALUES (?, ?, ?)',
                        (beds[0], msg, now),
                    )

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Simulation error: {e}")


# ── API routes ──────────────────────────────────────────────────────────

def generate_ecg_waveform(hr, rhythm, num_points=200):
    """Generate a simulated ECG waveform as a list of y-values."""
    points = []
    beats_per_sec = hr / 60.0
    duration = 4.0  # seconds of ECG
    for i in range(num_points):
        t = (i / num_points) * duration
        phase = (t * beats_per_sec) % 1.0
        # Simulate PQRST complex
        y = 0.0
        if 0.0 <= phase < 0.05:       # P wave
            y = 0.15 * math.sin(math.pi * phase / 0.05)
        elif 0.08 <= phase < 0.10:    # Q dip
            y = -0.1 * math.sin(math.pi * (phase - 0.08) / 0.02)
        elif 0.10 <= phase < 0.16:    # R peak
            y = 1.0 * math.sin(math.pi * (phase - 0.10) / 0.06)
        elif 0.16 <= phase < 0.20:    # S dip
            y = -0.25 * math.sin(math.pi * (phase - 0.16) / 0.04)
        elif 0.28 <= phase < 0.40:    # T wave
            y = 0.25 * math.sin(math.pi * (phase - 0.28) / 0.12)
        # Add noise for realism
        if 'Fibrillation' in rhythm:
            y += random.uniform(-0.08, 0.08)
        else:
            y += random.uniform(-0.02, 0.02)
        points.append(round(y, 4))
    return points


@app.route('/view', methods=['GET'])
def view():
    conn = get_db()
    patients = conn.execute('SELECT * FROM patients').fetchall()
    alerts = conn.execute(
        'SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 20'
    ).fetchall()
    beds = conn.execute('SELECT * FROM bed_availability ORDER BY bed_id').fetchall()
    nurses = conn.execute('SELECT * FROM nurse_assignments ORDER BY nurse_id').fetchall()
    conn.close()
    return jsonify({
        "patients": [dict(p) for p in patients],
        "alerts": [dict(a) for a in alerts],
        "beds": [dict(b) for b in beds],
        "nurses": [dict(n) for n in nurses],
        "server_time": ottawa_now(),
    })


@app.route('/patient/<bed_id>', methods=['GET'])
def patient_detail(bed_id):
    conn = get_db()
    patient = conn.execute(
        'SELECT * FROM patients WHERE bed_id = ?', (bed_id,)
    ).fetchone()
    if patient is None:
        conn.close()
        return jsonify({"error": "Patient not found"}), 404
    alerts = conn.execute(
        'SELECT * FROM alerts WHERE bed_id = ? ORDER BY timestamp DESC LIMIT 50',
        (bed_id,),
    ).fetchall()
    conn.close()
    p = dict(patient)
    ecg = generate_ecg_waveform(p['hr'], p.get('heart_rhythm', ''))
    return jsonify({
        "patient": p,
        "alerts": [dict(a) for a in alerts],
        "ecg": ecg,
        "server_time": ottawa_now(),
    })


@app.route('/beds', methods=['GET'])
def beds_view():
    """Return bed availability data."""
    conn = get_db()
    beds = conn.execute('SELECT * FROM bed_availability ORDER BY bed_id').fetchall()
    conn.close()

    bed_list = [dict(b) for b in beds]
    occupied = sum(1 for b in bed_list if b['is_occupied'])
    total = len(bed_list)

    return jsonify({
        "beds": bed_list,
        "total": total,
        "occupied": occupied,
        "available": total - occupied,
        "occupancy_rate": round((occupied / total) * 100, 1) if total else 0,
        "server_time": ottawa_now(),
    })


@app.route('/nurses', methods=['GET'])
def nurses_view():
    """Return nurse assignment data."""
    conn = get_db()
    nurses = conn.execute('SELECT * FROM nurse_assignments ORDER BY nurse_id').fetchall()
    conn.close()

    nurse_list = [dict(n) for n in nurses]
    overloaded = sum(1 for n in nurse_list if n['workload'] == 'Overloaded')
    high = sum(1 for n in nurse_list if n['workload'] == 'High')

    return jsonify({
        "nurses": nurse_list,
        "total": len(nurse_list),
        "overloaded": overloaded,
        "high_workload": high,
        "normal": len(nurse_list) - overloaded - high,
        "server_time": ottawa_now(),
    })


@app.route('/post_alert', methods=['POST'])
def post_alert():
    data = request.json
    conn = get_db()
    conn.execute(
        'INSERT INTO alerts (bed_id, message, timestamp) VALUES (?, ?, ?)',
        (data['bed_id'], data['alert'], ottawa_now()),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})


with app.app_context():
    init_db()

# Start the real-time simulation in a background daemon thread
sim_thread = threading.Thread(target=simulate_vitals, daemon=True)
sim_thread.start()
print("[OK] Real-time vitals simulation started (updates every 5s)")

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)