import os
import sys
import time
import requests
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import get_engine, TABLE_PATIENTS


def run_agent():
    engine = get_engine()
    print("--- Monitoring Agent Active ---")
    while True:
        try:
            with engine.connect() as conn:
                patients = [dict(r) for r in conn.execute(text(f'SELECT * FROM {TABLE_PATIENTS} LIMIT 10')).mappings().all()]
            for p in patients:
                if p.get('hr') and p['hr'] > 100:
                    alert = {"bed_id": p['bed_id'], "alert": f"High clinical value detected: HR={p['hr']}"}
                    requests.post("http://127.0.0.1:5000/post_alert", json=alert)
            print("Checked vitals... posting alerts if found.")
        except Exception as e:
            print(f"Waiting for data... {e}")
        time.sleep(5)

if __name__ == "__main__":
    run_agent()
