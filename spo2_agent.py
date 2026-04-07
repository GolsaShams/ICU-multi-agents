import os
import sys
import time
import requests
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import get_engine, TABLE_PATIENTS


class OxygenAgent:
    def __init__(self):
        self.engine = get_engine()
        self.api = "http://127.0.0.1:5000/post_alert"

    def run(self):
        print("Oxygen Agent is monitoring...")
        while True:
            try:
                with self.engine.connect() as conn:
                    patients = [dict(r) for r in conn.execute(text(f'SELECT bed_id, spo2 FROM {TABLE_PATIENTS}')).mappings().all()]
                for p in patients:
                    if p['spo2'] and p['spo2'] < 90:
                        print(f"Low Oxygen Alert: {p['bed_id']} ({p['spo2']}%)")
                        requests.post(self.api, json={
                            "bed_id": p['bed_id'],
                            "alert": f"Oxygenation Alert: Low SpO2 level detected ({p['spo2']}%)."
                        })
                time.sleep(5)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    agent = OxygenAgent()
    agent.run()
