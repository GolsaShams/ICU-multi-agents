import time
import sqlite3
import requests

class OxygenAgent:
    def __init__(self):
        self.db = 'icu_agents.db'
        self.api = "http://127.0.0.1:5000/post_alert"

    def run(self):
        print("Oxygen Agent is monitoring 'icu_agents.db'...")
        while True:
            try:
                conn = sqlite3.connect(self.db)
                conn.row_factory = sqlite3.Row
                patients = conn.execute('SELECT bed_id, spo2 FROM patients').fetchall()
                conn.close()

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