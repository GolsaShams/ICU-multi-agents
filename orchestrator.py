import os
import sys
import time
import requests
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import get_engine, TABLE_PATIENTS


class ICUOrchestrator:
    def __init__(self):
        self.engine = get_engine()
        self.api = "http://127.0.0.1:5000/post_alert"

    def run_analysis(self):
        print("--- ICU Central Orchestrator is Monitoring ---")
        while True:
            try:
                with self.engine.connect() as conn:
                    patients = [dict(r) for r in conn.execute(text(f'SELECT * FROM {TABLE_PATIENTS}')).mappings().all()]
                for p in patients:
                    bed = p['bed_id']
                    vitals_risk = p['hr'] > 100 and p['temp'] > 38.0
                    oxygen_risk = p['spo2'] < 90
                    cardiac_risk = p['heart_rhythm'] == 'Atrial Fibrillation'
                    if vitals_risk and oxygen_risk:
                        self.alert(bed, "CRITICAL: Combined Sepsis & Respiratory Failure!")
                    elif cardiac_risk and vitals_risk:
                        self.alert(bed, f"URGENT: Cardiac Arrhythmia ({p['heart_rhythm']}) with Fever.")
                    elif oxygen_risk:
                        self.alert(bed, f"Advisory: Low Oxygen Saturation ({p['spo2']}%).")
                    elif cardiac_risk:
                        self.alert(bed, f"Advisory: ECG Rhythm Abnormal ({p['heart_rhythm']}).")
                    elif vitals_risk:
                        self.alert(bed, "Advisory: Fever and High Heart Rate detected.")
                time.sleep(5)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

    def alert(self, bed, msg):
        requests.post(self.api, json={"bed_id": bed, "alert": msg})

if __name__ == "__main__":
    ICUOrchestrator().run_analysis()
