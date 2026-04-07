import os
import sys
import time
import requests
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import get_engine, TABLE_PATIENTS


class ECGAgent:
    def __init__(self):
        self.engine = get_engine()
        self.api = "http://127.0.0.1:5000/post_alert"

    def monitor_cardiac_rhythm(self):
        print("--- ECG Monitoring Agent is Active ---")
        while True:
            try:
                with self.engine.connect() as conn:
                    patients = [dict(r) for r in conn.execute(text(f'SELECT bed_id, hr, rhythm FROM {TABLE_PATIENTS}')).mappings().all()]
                for p in patients:
                    rhythm = p['rhythm']
                    hr = p['hr']
                    if rhythm == "Atrial Fibrillation":
                        requests.post(self.api, json={
                            "bed_id": p['bed_id'],
                            "alert": f"ECG Agent: AFib detected! Risk of stroke or heart failure."
                        })
                    elif rhythm == "Bradycardia" and hr < 50:
                        requests.post(self.api, json={
                            "bed_id": p['bed_id'],
                            "alert": f"ECG Agent: Critical Bradycardia (HR: {hr})."
                        })
                time.sleep(5)
            except Exception as e:
                print(f"ECG Agent Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    agent = ECGAgent()
    agent.monitor_cardiac_rhythm()
