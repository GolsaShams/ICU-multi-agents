import time
import sqlite3
import requests

class ECGAgent:
    def __init__(self):
        self.db = 'icu_agents.db'
        self.api = "http://127.0.0.1:5000/post_alert"

    def monitor_cardiac_rhythm(self):
        print("--- ECG Monitoring Agent is Active ---")
        while True:
            try:
                conn = sqlite3.connect(self.db)
                conn.row_factory = sqlite3.Row
                patients = conn.execute('SELECT bed_id, hr, heart_rhythm FROM patients').fetchall()
                conn.close()

                for p in patients:
                    rhythm = p['heart_rhythm']
                    hr = p['hr']
                    
                    # Logic: Trigger alert for dangerous rhythms
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