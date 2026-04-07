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
    print("AI Agent is watching bed_01...")
    while True:
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f'SELECT * FROM {TABLE_PATIENTS} WHERE bed_id=:bed'), {'bed': 'bed_01'}).mappings().all()
            if result:
                p = dict(result[0])
                if p['hr'] > 100 and p['temp'] > 38.0:
                    requests.post("http://127.0.0.1:5000/post_alert", json={
                        "bed_id": "bed_01",
                        "alert": f"CRITICAL: High HR ({p['hr']}) and Temp ({p['temp']})"
                    })
            time.sleep(2)
        except:
            time.sleep(2)

if __name__ == "__main__":
    run_agent()
