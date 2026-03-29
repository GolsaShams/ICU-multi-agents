import sqlite3
import time
import requests
import pandas as pd

def run_agent():
    print("--- Monitoring Agent Active ---")
    while True:
        conn = sqlite3.connect('icu_database.db')
        # We query the real vitals you just imported
        try:
            df = pd.read_sql("SELECT * FROM mimic_vitals LIMIT 10", conn)
            for _, row in df.iterrows():
                val = row['valuenum']
                # If a high value is found, send it to the Blackboard
                if val > 100:
                    alert = {"bed_id": "bed_01", "alert": f"High clinical value detected: {val}"}
                    requests.post("http://127.0.0.1:5000/post_alert", json=alert)
            print("Checked vitals... posting alerts if found.")
        except Exception as e:
            print(f"Waiting for data... {e}")
        
        conn.close()
        time.sleep(5) # Check every 5 seconds

if __name__ == "__main__":
    run_agent()