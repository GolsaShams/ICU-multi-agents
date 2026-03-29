import time
import sqlite3
import requests

class ICUOrchestrator:
    def __init__(self):
        self.db = 'icu_agents.db'
        self.api = "http://127.0.0.1:5000/post_alert"

    def run_analysis(self):
        print("--- ICU Central Orchestrator is Monitoring ---")
        while True:
            try:
                conn = sqlite3.connect(self.db)
                conn.row_factory = sqlite3.Row
                patients = conn.execute('SELECT * FROM patients').fetchall()
                conn.close()

                for p in patients:
                    bed = p['bed_id']
                    
                    # 1. Vitals Logic (Sepsis)
                    vitals_risk = p['hr'] > 100 and p['temp'] > 38.0
                    
                    # 2. Oxygenation Logic (Hypoxemia)
                    oxygen_risk = p['spo2'] < 90
                    
                    # 3. ECG Logic (Arrhythmia)
                    cardiac_risk = p['heart_rhythm'] == 'Atrial Fibrillation'

                    # --- Orchestration / Data Fusion ---
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